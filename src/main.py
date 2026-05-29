#!/usr/bin/env python3
import sys
from pathlib import Path

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

from analyzers.change_analyzer import ChangeAnalyzer

from reporters.console_reporter import ConsoleReporter


def main():
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
    last_timestamp = previous_run['timestamp'] if previous_run else None

    scan_collector = ScanCollector(client)
    asset_collector = AssetCollector(client)
    agent_collector = AgentCollector(client, thresholds.get('agent_offline_days', 14))
    scanner_collector = ScannerCollector(client)
    connector_collector = ConnectorCollector(client)

    logger.info("  • Collecting scan data...")
    scan_data = scan_collector.collect(last_timestamp)

    logger.info("  • Collecting asset data...")
    asset_data = asset_collector.collect()

    logger.info("  • Collecting agent data...")
    agent_data = agent_collector.collect()

    logger.info("  • Collecting scanner data...")
    scanner_data = scanner_collector.collect()

    logger.info("  • Collecting connector data...")
    connector_data = connector_collector.collect()

    current_data = {
        'scans': scan_data,
        'assets': asset_data,
        'agents': agent_data,
        'scanners': scanner_data,
        'connectors': connector_data
    }

    logger.info("\nAnalyzing changes...")
    analyzer = ChangeAnalyzer(thresholds)

    analysis_results = {
        'scans': analyzer.analyze_scans(scan_data, previous_run),
        'assets': analyzer.analyze_credentials(asset_data, previous_run),
        'license': analyzer.analyze_license(asset_data, previous_run),
        'agents': analyzer.analyze_agents(agent_data, previous_run),
        'scanners': analyzer.analyze_scanners(scanner_data, previous_run),
        'connectors': analyzer.analyze_connectors(connector_data, previous_run)
    }

    logger.info("\nSaving results...")
    # Save data without Claude analysis (will be generated during report creation)
    run_data = {
        'data': current_data
    }
    storage.save_run_data(run_data)

    # Save trend data for long-term charting
    trends.add_data_point(current_data)

    logger.info("\n")

    reporter = ConsoleReporter()
    reporter.print_header()

    reporter.print_scans(scan_data, analysis_results['scans'])
    reporter.print_assets(asset_data, analysis_results['assets'])
    reporter.print_license(asset_data, analysis_results['license'])
    reporter.print_agents(agent_data, analysis_results['agents'])
    reporter.print_scanners(scanner_data, analysis_results['scanners'])
    reporter.print_connectors(connector_data, analysis_results['connectors'])

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
