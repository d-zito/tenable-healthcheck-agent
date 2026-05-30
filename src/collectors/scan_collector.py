from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger('tenable-healthcheck')


class ScanCollector:
    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self, days_back=7):
        """
        Collect scan health data for the past N days.

        Args:
            days_back: Number of days to look back (default 7)

        Returns:
            dict with scan statistics and history
        """
        scans_data = self.client.get_scans()
        scans = scans_data.get('scans', [])

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_timestamp = int(cutoff_time.timestamp())

        total_launches = 0
        currently_running = 0
        scan_summary = {}  # {scan_name: {total_runs: X, failed_runs: Y}}

        logger.info(f"    Analyzing scan history for past {days_back} days...")

        for scan in scans:
            scan_id = scan.get('id')
            scan_name = scan.get('name')

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
                    failed_runs = sum(
                        1 for h in recent_history
                        if h.get('status', '').lower() not in ['completed', 'running']
                    )

                    total_launches += total_runs

                    scan_summary[scan_name] = {
                        'scan_id': scan_id,
                        'total_runs': total_runs,
                        'failed_runs': failed_runs,
                        'success_runs': total_runs - failed_runs
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
