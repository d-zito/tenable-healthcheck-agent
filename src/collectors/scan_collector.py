from datetime import datetime, timedelta, timezone


class ScanCollector:
    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self, last_run_timestamp=None):
        scans_data = self.client.get_scans()
        scans = scans_data.get('scans', [])

        if last_run_timestamp:
            last_run_dt = datetime.fromisoformat(last_run_timestamp)
            scans = [s for s in scans if self._is_scan_new(s, last_run_dt)]

        problem_scans = []
        completed_scans = []

        for scan in scans:
            status = scan.get('status', '').lower()

            if status in ['aborted', 'stopped', 'canceled']:
                problem_scans.append({
                    'id': scan.get('id'),
                    'name': scan.get('name'),
                    'status': status,
                    'last_modification_date': scan.get('last_modification_date')
                })
            elif status == 'completed':
                completed_scans.append({
                    'id': scan.get('id'),
                    'name': scan.get('name'),
                    'status': status,
                    'last_modification_date': scan.get('last_modification_date')
                })

        return {
            'total_scans': len(scans),
            'problem_scans': problem_scans,
            'completed_scans': completed_scans,
            'scans_checked_since': last_run_timestamp
        }

    def _is_scan_new(self, scan, last_run_dt):
        """Check if scan was modified after the last run timestamp."""
        modification_timestamp = scan.get('last_modification_date')
        if not modification_timestamp:
            return False

        # Convert Unix timestamp to timezone-aware UTC datetime
        scan_dt = datetime.fromtimestamp(modification_timestamp, tz=timezone.utc)

        # Parse last_run_dt if it's a string (ISO format from storage)
        if isinstance(last_run_dt, str):
            # Handle ISO format with timezone info
            last_run_dt = datetime.fromisoformat(last_run_dt)
            # Ensure it's timezone-aware (add UTC if naive)
            if last_run_dt.tzinfo is None:
                last_run_dt = last_run_dt.replace(tzinfo=timezone.utc)
        elif last_run_dt.tzinfo is None:
            # If it's already a datetime but naive, make it aware
            last_run_dt = last_run_dt.replace(tzinfo=timezone.utc)

        return scan_dt > last_run_dt
