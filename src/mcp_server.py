#!/usr/bin/env python3
"""
MCP server for Tenable Health Check Agent.
Exposes health check data and analysis as MCP tools for use in Claude Code.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure src/ modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from storage.storage_manager import StorageManager
from analyzers.change_analyzer import ChangeAnalyzer
from config_loader import ConfigLoader

mcp = FastMCP("tenable-healthcheck")

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "history"


def _get_storage() -> StorageManager:
    return StorageManager(data_dir=DATA_DIR)


def _get_run_timestamp(run_data: dict[str, Any]) -> str:
    return run_data.get("timestamp", "unknown")


def _list_run_files() -> list[Path]:
    return sorted(DATA_DIR.glob("healthcheck_*.json"))


@mcp.tool()
def list_runs(limit: int = 10) -> str:
    """
    List available health check runs stored locally.

    Args:
        limit: Maximum number of runs to return (most recent first). Default 10.

    Returns:
        JSON array of run entries with timestamp and filename.
    """
    files = _list_run_files()
    files = files[-limit:][::-1]  # most recent first

    runs = []
    for f in files:
        stamp = f.stem.replace("healthcheck_", "")
        runs.append({"timestamp_id": stamp, "filename": f.name})

    return json.dumps(runs, indent=2)


@mcp.tool()
def get_raw_data(timestamp_id: str = "") -> str:
    """
    Return the raw collected data from a health check run.

    Args:
        timestamp_id: The run timestamp ID (e.g. '20260805_103045'). Leave empty to use the latest run.

    Returns:
        JSON object with the full raw data payload for that run.
    """
    if timestamp_id:
        filepath = DATA_DIR / f"healthcheck_{timestamp_id}.json"
        if not filepath.exists():
            return json.dumps({"error": f"Run not found: {timestamp_id}"})
        with open(filepath) as f:
            return f.read()

    storage = _get_storage()
    latest = storage.get_latest_run()
    if latest is None:
        return json.dumps({"error": "No runs found. Run the health check first."})
    return json.dumps(latest, indent=2)


@mcp.tool()
def get_summary(timestamp_id: str = "") -> str:
    """
    Return an AI-generated summary for a health check run, or compute one on the fly.

    If the run JSON already contains a cached 'claude_analysis', that is returned directly.
    Otherwise the analysis is computed from the raw data using the ChangeAnalyzer and
    returned without caching.

    Args:
        timestamp_id: The run timestamp ID. Leave empty to use the latest run.

    Returns:
        JSON object with health_status, executive_summary, key_concerns,
        recommendations, and trends fields.
    """
    if timestamp_id:
        filepath = DATA_DIR / f"healthcheck_{timestamp_id}.json"
        if not filepath.exists():
            return json.dumps({"error": f"Run not found: {timestamp_id}"})
        with open(filepath) as f:
            run_data = json.load(f)
    else:
        storage = _get_storage()
        run_data = storage.get_latest_run()
        if run_data is None:
            return json.dumps({"error": "No runs found. Run the health check first."})

    # Return cached AI analysis if available
    if "claude_analysis" in run_data:
        return json.dumps(run_data["claude_analysis"], indent=2)

    # Otherwise compute analysis from raw data
    try:
        config = ConfigLoader()
        thresholds = config.get_thresholds()
    except FileNotFoundError:
        thresholds = {}

    analyzer = ChangeAnalyzer(thresholds)
    current_data = run_data.get("data", {})

    # Load previous run for delta analysis
    files = _list_run_files()
    if timestamp_id:
        target = DATA_DIR / f"healthcheck_{timestamp_id}.json"
        try:
            idx = files.index(target)
            previous_data: dict[str, Any] | None = None
            if idx > 0:
                with open(files[idx - 1]) as f:
                    previous_data = json.load(f)
        except ValueError:
            previous_data = None
    else:
        storage = _get_storage()
        previous_data = storage.get_previous_run()

    analysis_results = {
        "scans": analyzer.analyze_scans(current_data.get("scans", {}), previous_data),
        "assets": analyzer.analyze_credentials(current_data.get("assets", {}), previous_data),
        "license": analyzer.analyze_license(current_data.get("assets", {}), previous_data),
        "agents": analyzer.analyze_agents(current_data.get("agents", {}), previous_data),
        "scanners": analyzer.analyze_scanners(current_data.get("scanners", {}), previous_data),
        "connectors": analyzer.analyze_connectors(current_data.get("connectors", {}), previous_data),
        "users": analyzer.analyze_users(current_data.get("users", {}), previous_data),
    }

    # Try AI analysis; fall back to structured summary without it
    try:
        from analyzers.claude_analyzer import ClaudeAnalyzer
        claude = ClaudeAnalyzer(config.config)  # type: ignore[possibly-undefined]
        ai_result = claude.analyze_health_report(current_data, analysis_results)
        return json.dumps(ai_result, indent=2)
    except Exception as e:
        # Return structured summary without AI narrative
        return json.dumps(
            {
                "health_status": "unknown",
                "executive_summary": f"AI analysis unavailable: {e}",
                "key_concerns": [],
                "recommendations": [],
                "trends": [],
                "analysis_results": {k: str(v) for k, v in analysis_results.items()},
            },
            indent=2,
        )


@mcp.tool()
def run_fresh_analysis() -> str:
    """
    Trigger a new Tenable health check data collection and save results locally.

    This calls the main health check agent (src/main.py) as a subprocess, waits
    for it to complete, then returns the summary of the newly saved run.

    Returns:
        JSON object with outcome status and the resulting run summary,
        or an error message if the collection fails.
    """
    main_script = Path(__file__).parent / "main.py"
    if not main_script.exists():
        return json.dumps({"error": "main.py not found next to mcp_server.py"})

    result = subprocess.run(
        [sys.executable, str(main_script)],
        capture_output=True,
        text=True,
        cwd=str(main_script.parent),
    )

    if result.returncode != 0:
        return json.dumps(
            {
                "error": "Health check collection failed",
                "returncode": result.returncode,
                "stderr": result.stderr[-2000:] if result.stderr else "",
                "stdout": result.stdout[-2000:] if result.stdout else "",
            }
        )

    # Return the summary of the newly saved run
    summary_json = get_summary()
    return json.dumps(
        {
            "status": "success",
            "message": "Fresh health check completed and saved.",
            "summary": json.loads(summary_json),
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
