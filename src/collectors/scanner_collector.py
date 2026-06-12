from __future__ import annotations

from typing import Any

from tenable_client import TenableClient


class ScannerCollector:
    def __init__(self, tenable_client: TenableClient) -> None:
        self.client = tenable_client

    def collect(self) -> dict[str, Any]:
        """
        Collect scanner health data.

        Only includes 'managed' scanners (user-managed), excluding 'local'
        scanners which are hosted by Tenable.
        """
        all_scanners = self.client.list_scanners()

        scanners = [s for s in all_scanners if s.get('type') == 'managed']

        total_scanners = len(scanners)
        working_scanners = 0
        problem_scanners: list[dict[str, Any]] = []

        for scanner in scanners:
            status = scanner.get('status', '').lower()
            scan_count = scanner.get('scan_count', 0)

            if status in ('on', 'working'):
                working_scanners += 1
            else:
                problem_scanners.append({
                    'id': scanner.get('id'),
                    'name': scanner.get('name'),
                    'status': status,
                    'type': scanner.get('type'),
                    'scan_count': scan_count,
                    'last_connect': scanner.get('last_connect'),
                    'last_modification_date': scanner.get('last_modification_date'),
                })

        return {
            'total_scanners': total_scanners,
            'working_scanners': working_scanners,
            'problem_scanners': len(problem_scanners),
            'problem_scanner_list': problem_scanners,
        }
