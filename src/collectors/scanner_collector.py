class ScannerCollector:
    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self):
        scanners = self.client.list_scanners()

        total_scanners = len(scanners)
        working_scanners = 0
        problem_scanners = []

        for scanner in scanners:
            status = scanner.get('status', '').lower()
            scan_count = scanner.get('scan_count', 0)

            if status == 'on' or status == 'working':
                working_scanners += 1
            else:
                problem_scanners.append({
                    'id': scanner.get('id'),
                    'name': scanner.get('name'),
                    'status': status,
                    'type': scanner.get('type'),
                    'scan_count': scan_count,
                    'last_connect': scanner.get('last_connect'),
                    'last_modification_date': scanner.get('last_modification_date')
                })

        return {
            'total_scanners': total_scanners,
            'working_scanners': working_scanners,
            'problem_scanners': len(problem_scanners),
            'problem_scanner_list': problem_scanners
        }
