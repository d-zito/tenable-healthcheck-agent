from datetime import datetime, timedelta


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
        modification_timestamp = scan.get('last_modification_date')
        if not modification_timestamp:
            return False

        scan_dt = datetime.fromtimestamp(modification_timestamp)
        return scan_dt > last_run_dt
