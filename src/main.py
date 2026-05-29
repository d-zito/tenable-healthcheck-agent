#!/usr/bin/env python3
import sys
from pathlib import Path

from config_loader import ConfigLoader
from tenable_client import TenableClient
from storage.storage_manager import StorageManager

from collectors.scan_collector import ScanCollector
from collectors.asset_collector import AssetCollector
from collectors.license_collector import LicenseCollector
from collectors.agent_collector import AgentCollector
from collectors.scanner_collector import ScannerCollector
from collectors.connector_collector import ConnectorCollector

from analyzers.change_analyzer import ChangeAnalyzer
from analyzers.claude_analyzer import ClaudeAnalyzer

from reporters.console_reporter import ConsoleReporter


def main():
    print("Starting Tenable One Health Check Agent...")
    print()

    try:
        config = ConfigLoader()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    creds = config.get_tenable_credentials()
    client = TenableClient(
        access_key=creds['access_key'],
        secret_key=creds['secret_key'],
        base_url=creds['base_url']
    )

    storage = StorageManager(retention_days=config.get_data_retention_days())
    thresholds = config.get_thresholds()

    print("Collecting data from Tenable One...")
    print()

    previous_run = storage.get_previous_run()
    last_timestamp = previous_run['timestamp'] if previous_run else None

    scan_collector = ScanCollector(client)
    asset_collector = AssetCollector(client)
    license_collector = LicenseCollector(client)
    agent_collector = AgentCollector(client, thresholds.get('agent_offline_days', 14))
    scanner_collector = ScannerCollector(client)
    connector_collector = ConnectorCollector(client)

    print("  • Collecting scan data...")
    scan_data = scan_collector.collect(last_timestamp)

    print("  • Collecting asset data...")
    asset_data = asset_collector.collect()

    print("  • Collecting license data...")
    license_data = license_collector.collect()

    print("  • Collecting agent data...")
    agent_data = agent_collector.collect()

    print("  • Collecting scanner data...")
    scanner_data = scanner_collector.collect()

    print("  • Collecting connector data...")
    connector_data = connector_collector.collect()

    current_data = {
        'scans': scan_data,
        'assets': asset_data,
        'license': license_data,
        'agents': agent_data,
        'scanners': scanner_data,
        'connectors': connector_data
    }

    print("\nAnalyzing changes...")
    analyzer = ChangeAnalyzer(thresholds)

    analysis_results = {
        'scans': analyzer.analyze_scans(scan_data, previous_run),
        'assets': analyzer.analyze_credentials(asset_data, previous_run),
        'license': analyzer.analyze_license(license_data, previous_run),
        'agents': analyzer.analyze_agents(agent_data, previous_run),
        'scanners': analyzer.analyze_scanners(scanner_data, previous_run),
        'connectors': analyzer.analyze_connectors(connector_data, previous_run)
    }

    print("Running AI analysis with Claude...")
    claude = ClaudeAnalyzer(use_cli=config.use_claude_cli())
    claude_results = claude.analyze_health_report(current_data, analysis_results)

    print("\nSaving results...")
    # Save data with Claude analysis included
    run_data_with_analysis = {
        'data': current_data,
        'claude_analysis': claude_results
    }
    storage.save_run_data(run_data_with_analysis)

    print("\n")

    reporter = ConsoleReporter()
    reporter.print_header()

    reporter.print_scans(scan_data, analysis_results['scans'])
    reporter.print_assets(asset_data, analysis_results['assets'])
    reporter.print_license(license_data, analysis_results['license'])
    reporter.print_agents(agent_data, analysis_results['agents'])
    reporter.print_scanners(scanner_data, analysis_results['scanners'])
    reporter.print_connectors(connector_data, analysis_results['connectors'])

    reporter.print_claude_analysis(claude_results)

    reporter.print_footer()

    print("\nHealth check complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nHealth check interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
