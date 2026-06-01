from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger('tenable-healthcheck')


class ScanCollector:
    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self, days_back=7, previous_run_data=None):
        """
        Collect scan health data for the past N days.

        Args:
            days_back: Number of days to look back (default 7)
            previous_run_data: Previous run data for caching policy info

        Returns:
            dict with scan statistics and history
        """
        scans_data = self.client.get_scans()
        scans = scans_data.get('scans', [])

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_timestamp = int(cutoff_time.timestamp())

        # Get previous scan data for policy caching
        previous_scan_summary = {}
        if previous_run_data:
            previous_scan_summary = previous_run_data.get('data', {}).get('scans', {}).get('scan_summary', {})

        total_launches = 0
        currently_running = 0
        scan_summary = {}  # {scan_name: {total_runs: X, failed_runs: Y}}

        logger.info(f"    Analyzing scan history for past {days_back} days...")

        for scan in scans:
            scan_id = scan.get('id')
            scan_name = scan.get('name')
            last_modification_date = scan.get('last_modification_date', 0)

            # Check if we need to fetch scan details (enabled status and policy)
            # Only fetch if scan was modified since last run, or we don't have cached data
            need_details = True
            cached_policy = None
            cached_enabled = True

            if scan_name in previous_scan_summary:
                previous_scan_data = previous_scan_summary[scan_name]
                previous_last_mod = previous_scan_data.get('last_modification_date', 0)

                # If scan hasn't been modified, use cached data
                if last_modification_date == previous_last_mod:
                    need_details = False
                    cached_policy = previous_scan_data.get('policy')
                    cached_enabled = previous_scan_data.get('is_enabled', True)
                    logger.debug(f"    Using cached data for scan '{scan_name}' (no modifications)")

            is_scan_enabled = cached_enabled
            policy_name = cached_policy

            if need_details:
                try:
                    # Use results() to get info section with policy
                    scan_results = self.client.tio.scans.results(scan_id)
                    info = scan_results.get('info', {})
                    policy_name = info.get('policy', None)

                    # Get enabled status from details() settings section
                    scan_details = self.client.get_scan_details(scan_id)
                    settings = scan_details.get('settings', {})
                    is_scan_enabled = settings.get('enabled', True)

                    logger.debug(f"    Fetched details for scan '{scan_name}': policy={policy_name}, enabled={is_scan_enabled}")
                except Exception as e:
                    logger.debug(f"    Could not get scan details for '{scan_name}': {e}")

            # Get scan history using pytenable's history() method
            try:
                # Get all history entries for this scan
                history_iter = self.client.tio.scans.history(scan_id)

                recent_history = []
                has_running = False

                for history_entry in history_iter:
                    time_start = history_entry.get('time_start', 0)
                    status = history_entry.get('status', '').lower()

                    # Check if this scan run is currently running
                    if status == 'running':
                        has_running = True

                    # Filter to past N days based on time_start
                    if time_start >= cutoff_timestamp:
                        recent_history.append(history_entry)

                # Count currently running scans
                if has_running:
                    currently_running += 1

                # Process recent history
                if recent_history:
                    total_runs = len(recent_history)

                    # Categorize statuses
                    completed_runs = 0
                    failed_runs = 0
                    stopped_runs = 0
                    disabled_runs = 0
                    canceled_runs = 0
                    paused_runs = 0
                    running_count = 0
                    disabled_entries = []

                    for h in recent_history:
                        status = h.get('status', '').lower()
                        time_start = h.get('time_start', 0)

                        if status == 'completed':
                            completed_runs += 1
                        elif status == 'running':
                            running_count += 1
                        elif status == 'disabled':
                            disabled_runs += 1
                            # Store disabled entry with date
                            disabled_entries.append({
                                'date': datetime.fromtimestamp(time_start).strftime('%Y-%m-%d') if time_start else 'Unknown',
                                'timestamp': time_start
                            })
                        elif status == 'stopped':
                            stopped_runs += 1
                        elif status in ['canceled', 'cancelled']:
                            canceled_runs += 1
                        elif status == 'paused':
                            paused_runs += 1
                        elif status in ['aborted', 'error', 'failed']:
                            # Actual failures
                            failed_runs += 1
                        else:
                            # Unknown status - log it and count as potential failure
                            logger.debug(f"    Unknown scan status '{status}' for scan '{scan_name}'")
                            failed_runs += 1

                    total_launches += total_runs

                    scan_summary[scan_name] = {
                        'scan_id': scan_id,
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
                        'success_runs': completed_runs  # Only completed = success
                    }

            except Exception as e:
                logger.warning(f"    Could not retrieve history for scan '{scan_name}': {e}")
                continue

        return {
            'days_back': days_back,
            'total_launches': total_launches,
            'currently_running': currently_running,
            'unique_scans': len(scan_summary),
            'scan_summary': scan_summary
        }
