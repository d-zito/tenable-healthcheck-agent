#!/usr/bin/env python3
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from logger import setup_logger
from config_loader import ConfigLoader
from tenable_client import TenableClient
from storage.storage_manager import StorageManager
from storage.trends_manager import TrendsManager

logger = setup_logger()

from collectors.scan_collector import ScanCollector
from collectors.asset_collector import AssetCollector
from collectors.agent_collector import AgentCollector
from collectors.scanner_collector import ScannerCollector
from collectors.connector_collector import ConnectorCollector
from collectors.user_collector import UserCollector

from analyzers.change_analyzer import ChangeAnalyzer

from reporters.console_reporter import ConsoleReporter


def main() -> None:
    logger.info("Starting Tenable One Health Check Agent...")
    logger.info("")

    try:
        config = ConfigLoader()
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    creds = config.get_tenable_credentials()
    client = TenableClient(
        access_key=creds['access_key'],
        secret_key=creds['secret_key'],
        base_url=creds['base_url']
    )

    storage = StorageManager(retention_days=config.get_data_retention_days())
    trends = TrendsManager()
    thresholds = config.get_thresholds()

    logger.info("Collecting data from Tenable One...")
    logger.info("")

    previous_run = storage.get_previous_run()

    scan_collector = ScanCollector(client)
    asset_collector = AssetCollector(client)
    agent_collector = AgentCollector(client, thresholds.get('agent_offline_days', 14))
    scanner_collector = ScannerCollector(client)
    connector_collector = ConnectorCollector(client)
    user_collector = UserCollector(client)

    # Collect data in parallel where possible
    # Scan collector needs previous_run_data so it runs with its own args
    current_data: dict[str, Any] = {}

    def collect_scans() -> tuple[str, Any]:
        logger.info("  • Collecting scan data (past 30 days)...")
        return ('scans', scan_collector.collect(days_back=30, previous_run_data=previous_run))

    def collect_assets() -> tuple[str, Any]:
        logger.info("  • Collecting asset data...")
        return ('assets', asset_collector.collect())

    def collect_agents() -> tuple[str, Any]:
        logger.info("  • Collecting agent data...")
        return ('agents', agent_collector.collect())

    def collect_scanners() -> tuple[str, Any]:
        logger.info("  • Collecting scanner data...")
        return ('scanners', scanner_collector.collect())

    def collect_connectors() -> tuple[str, Any]:
        logger.info("  • Collecting connector data...")
        return ('connectors', connector_collector.collect())

    def collect_users() -> tuple[str, Any]:
        logger.info("  • Collecting user data...")
        return ('users', user_collector.collect())

    collectors = [collect_scans, collect_assets, collect_agents, collect_scanners, collect_connectors, collect_users]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): fn.__name__ for fn in collectors}
        for future in as_completed(futures):
            try:
                key, data = future.result()
                current_data[key] = data
            except Exception as e:
                fn_name = futures[future]
                logger.error(f"Collector {fn_name} failed: {type(e).__name__}: {e}")

    logger.info("\nAnalyzing changes...")
    analyzer = ChangeAnalyzer(thresholds)

    analysis_results = {
        'scans': analyzer.analyze_scans(current_data.get('scans', {}), previous_run),
        'assets': analyzer.analyze_credentials(current_data.get('assets', {}), previous_run),
        'license': analyzer.analyze_license(current_data.get('assets', {}), previous_run),
        'agents': analyzer.analyze_agents(current_data.get('agents', {}), previous_run),
        'scanners': analyzer.analyze_scanners(current_data.get('scanners', {}), previous_run),
        'connectors': analyzer.analyze_connectors(current_data.get('connectors', {}), previous_run),
        'users': analyzer.analyze_users(current_data.get('users', {}), previous_run),
    }

    logger.info("\nSaving results...")
    run_data: dict[str, Any] = {'data': current_data}
    storage.save_run_data(run_data)

    trends.add_data_point(current_data)

    logger.info("\n")

    reporter = ConsoleReporter()
    reporter.print_header()

    reporter.print_scans(current_data.get('scans', {}), analysis_results['scans'])
    reporter.print_assets(current_data.get('assets', {}), analysis_results['assets'])
    reporter.print_license(current_data.get('assets', {}), analysis_results['license'])
    reporter.print_agents(current_data.get('agents', {}), analysis_results['agents'])
    reporter.print_scanners(current_data.get('scanners', {}), analysis_results['scanners'])
    reporter.print_connectors(current_data.get('connectors', {}), analysis_results['connectors'])
    reporter.print_users(current_data.get('users', {}), analysis_results['users'])

    reporter.print_footer()

    logger.info("\nHealth check complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n\nHealth check interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nERROR: {e}", exc_info=True)
        sys.exit(1)
