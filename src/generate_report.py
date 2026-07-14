#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from reporters.html_reporter import HTMLReporter
from analyzers.change_analyzer import ChangeAnalyzer
from config_loader import ConfigLoader
from storage.trends_manager import TrendsManager


def get_latest_run(data_dir: Path) -> Path | None:
    files = sorted(data_dir.glob('healthcheck_*.json'))
    if not files:
        return None
    return files[-1]


def get_previous_run(data_dir: Path, current_file: Path) -> Path | None:
    files = sorted(data_dir.glob('healthcheck_*.json'))
    try:
        current_idx = files.index(current_file)
        if current_idx > 0:
            return files[current_idx - 1]
    except (ValueError, IndexError):
        pass
    return None


def load_run_data(filepath: Path) -> dict[str, Any]:
    with open(filepath, 'r') as f:
        return json.load(f)


def save_run_data(filepath: Path, data: dict[str, Any]) -> None:
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate HTML report from Tenable health check data'
    )
    parser.add_argument('--file', help='Path to specific JSON data file', type=Path)
    parser.add_argument('--date', help='Date/time stamp of run (e.g., 20260528_103045)', type=str)
    parser.add_argument('--output', help='Output HTML file path (default: reports/healthcheck_TIMESTAMP.html)', type=Path)
    parser.add_argument('--skip-ai', action='store_true', help='Skip AI analysis (use cached analysis from JSON file)')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "history"
    reports_dir = base_dir / "reports"

    reports_dir.mkdir(exist_ok=True)

    if args.file:
        data_file = args.file
    elif args.date:
        data_file = data_dir / f"healthcheck_{args.date}.json"
    else:
        data_file = get_latest_run(data_dir)

    if not data_file or not data_file.exists():
        print(f"ERROR: Data file not found: {data_file}")
        print(f"\nAvailable runs:")
        for f in sorted(data_dir.glob('healthcheck_*.json')):
            timestamp = f.stem.replace('healthcheck_', '')
            print(f"  {timestamp}")
        sys.exit(1)

    print(f"Loading data from: {data_file}")
    run_data = load_run_data(data_file)

    previous_file = get_previous_run(data_dir, data_file)
    previous_data = load_run_data(previous_file) if previous_file else None

    if previous_data:
        print(f"Loading previous run from: {previous_file}")

    config = ConfigLoader()
    thresholds = config.get_thresholds()

    print("Analyzing data...")
    analyzer = ChangeAnalyzer(thresholds)
    current_data = run_data.get('data', {})

    analysis_results = {
        'scans': analyzer.analyze_scans(current_data.get('scans', {}), previous_data),
        'assets': analyzer.analyze_credentials(current_data.get('assets', {}), previous_data),
        'license': analyzer.analyze_license(current_data.get('assets', {}), previous_data),
        'agents': analyzer.analyze_agents(current_data.get('agents', {}), previous_data),
        'scanners': analyzer.analyze_scanners(current_data.get('scanners', {}), previous_data),
        'connectors': analyzer.analyze_connectors(current_data.get('connectors', {}), previous_data),
        'users': analyzer.analyze_users(current_data.get('users', {}), previous_data),
    }

    if args.skip_ai:
        print("\n  Test mode: Skipping AI analysis (using cached data from JSON)")
        claude_analysis = run_data.get('claude_analysis')
        if not claude_analysis:
            print("  WARNING: No cached AI analysis found in this data file.")
            print("   Run without --skip-ai flag first to generate and cache AI analysis.")
            claude_analysis = None
    else:
        print("Running AI analysis...")
        from analyzers.claude_analyzer import ClaudeAnalyzer
        claude = ClaudeAnalyzer(config.config)
        claude_analysis = claude.analyze_health_report(current_data, analysis_results)

        print("Caching AI analysis to data file for future testing...")
        run_data['claude_analysis'] = claude_analysis
        save_run_data(data_file, run_data)

    print("Generating HTML report...")

    trends_manager = TrendsManager()
    trends_data = trends_manager.get_trends(daily_aggregation=True)

    reporter = HTMLReporter()
    html_content = reporter.generate(run_data, analysis_results, claude_analysis, trends_data)

    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = reports_dir / f"healthcheck_{timestamp}.html"

    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"\n  HTML report generated: {output_file}")
    print(f"\nOpen in browser:")
    print(f"  open {output_file}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nReport generation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
