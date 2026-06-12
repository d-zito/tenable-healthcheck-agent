from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from tenable_client import TenableClient

logger = logging.getLogger('tenable-healthcheck')


class ScanCollector:
    def __init__(self, tenable_client: TenableClient) -> None:
        self.client = tenable_client

    def collect(self, days_back: int = 7, previous_run_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Collect scan health data for the past N days."""
        scans = list(self.client.tio.scans.list())

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_timestamp = int(cutoff_time.timestamp())

        previous_scan_summary: dict[str, Any] = {}
        if previous_run_data:
            previous_scan_summary = previous_run_data.get('data', {}).get('scans', {}).get('scan_summary', {})

        total_launches = 0
        currently_running = 0
        scan_summary: dict[str, dict[str, Any]] = {}
        total_scans = 0
        inactive_scans = 0

        logger.info(f"    Analyzing scan history for past {days_back} days...")

        for scan in scans:
            scan_id = scan.get('id')
            scan_name = scan.get('name')
            last_modification_date = scan.get('last_modification_date', 0)
            policy_id = scan.get('policy_id')
            is_scan_enabled = scan.get('enabled', True)

            if scan.get('status') == 'deleted' or scan.get('is_deleted') or scan.get('trash'):
                logger.debug(f"    Skipping deleted scan '{scan_name}'")
                continue

            total_scans += 1

            need_details = True
            cached_policy: str | None = None
            cached_scan_type: str | None = None
            cached_agent_launch_type: str | None = None

            if scan_name in previous_scan_summary:
                previous_scan_data = previous_scan_summary[scan_name]
                previous_last_mod = previous_scan_data.get('last_modification_date', 0)

                if last_modification_date == previous_last_mod:
                    cached_policy = previous_scan_data.get('policy')
                    cached_scan_type = previous_scan_data.get('scan_type')
                    cached_agent_launch_type = previous_scan_data.get('agent_scan_launch_type')

                    if 'scan_type' in previous_scan_data and 'agent_scan_launch_type' in previous_scan_data:
                        need_details = False
                        logger.debug(f"    Using cached data for scan '{scan_name}' (no modifications)")
                    else:
                        logger.debug(f"    Fetching scan details for '{scan_name}' (missing fields in cache)")

            policy_name = cached_policy
            scan_type = cached_scan_type
            agent_scan_launch_type = cached_agent_launch_type

            if not policy_name and policy_id:
                try:
                    policy_details = self.client.tio.policies.details(policy_id)
                    policy_name = policy_details.get('settings', {}).get('name', None)
                    logger.debug(f"    Retrieved policy for scan '{scan_name}': {policy_name}")
                except (KeyError, AttributeError, TypeError) as e:
                    logger.debug(f"    Could not get policy details for scan '{scan_name}' (policy_id={policy_id}): {e}")
                except Exception as e:
                    logger.warning(f"    Unexpected error getting policy details for scan '{scan_name}': {type(e).__name__}: {e}")

            if need_details:
                try:
                    scan_results = self.client.tio.scans.results(scan_id)
                    info = scan_results.get('info', {})
                    scan_type = info.get('scan_type')
                    agent_scan_launch_type = info.get('agent_scan_launch_type')
                    logger.debug(f"    Fetched details for scan '{scan_name}': type={scan_type}, agent_launch={agent_scan_launch_type}")
                except (KeyError, AttributeError, TypeError) as e:
                    logger.debug(f"    Could not get scan results for '{scan_name}': {e}")
                except Exception as e:
                    logger.warning(f"    Unexpected error getting scan results for '{scan_name}': {type(e).__name__}: {e}")

            try:
                history_iter = self.client.tio.scans.history(scan_id)

                recent_history: list[dict[str, Any]] = []
                has_running = False

                for history_entry in history_iter:
                    time_start = history_entry.get('time_start', 0)
                    status = history_entry.get('status', '').lower()

                    if status == 'running':
                        has_running = True

                    if time_start >= cutoff_timestamp:
                        recent_history.append(history_entry)

                if has_running:
                    currently_running += 1

                total_runs = len(recent_history)

                completed_runs = 0
                failed_runs = 0
                stopped_runs = 0
                disabled_runs = 0
                canceled_runs = 0
                paused_runs = 0
                running_count = 0

                for h in recent_history:
                    status = h.get('status', '').lower()

                    if status == 'completed':
                        completed_runs += 1
                    elif status == 'running':
                        running_count += 1
                    elif status == 'disabled':
                        disabled_runs += 1
                    elif status == 'stopped':
                        stopped_runs += 1
                    elif status in ['canceled', 'cancelled']:
                        canceled_runs += 1
                    elif status == 'paused':
                        paused_runs += 1
                    elif status in ['aborted', 'error', 'failed']:
                        failed_runs += 1
                    else:
                        logger.debug(f"    Unknown scan status '{status}' for scan '{scan_name}'")
                        failed_runs += 1

                total_launches += total_runs

                if total_runs > 0:
                    scan_summary[scan_name] = {
                        'scan_id': scan_id,
                        'scan_type': scan_type,
                        'agent_scan_launch_type': agent_scan_launch_type,
                        'total_runs': total_runs,
                        'completed_runs': completed_runs,
                        'failed_runs': failed_runs,
                        'stopped_runs': stopped_runs,
                        'disabled_runs': disabled_runs,
                        'canceled_runs': canceled_runs,
                        'paused_runs': paused_runs,
                        'running_count': running_count,
                        'is_enabled': is_scan_enabled,
                        'policy': policy_name,
                        'last_modification_date': last_modification_date,
                        'success_runs': completed_runs,
                    }
                else:
                    inactive_scans += 1

            except (KeyError, AttributeError, TypeError, ValueError) as e:
                logger.warning(f"    Could not retrieve history for scan '{scan_name}': {type(e).__name__}: {e}")
                continue
            except Exception as e:
                logger.error(f"    Unexpected error processing scan '{scan_name}': {type(e).__name__}: {e}", exc_info=True)
                continue

        return {
            'days_back': days_back,
            'total_launches': total_launches,
            'currently_running': currently_running,
            'unique_scans': len(scan_summary),
            'total_scans': total_scans,
            'inactive_scans': inactive_scans,
            'scan_summary': scan_summary,
        }
