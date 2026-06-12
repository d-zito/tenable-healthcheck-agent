from __future__ import annotations

from typing import Any

from tenable_client import TenableClient


class ConnectorCollector:
    def __init__(self, tenable_client: TenableClient) -> None:
        self.client = tenable_client

    def collect(self) -> dict[str, Any]:
        connectors = self.client.list_connectors()

        total_connectors = len(connectors)
        working_connectors = 0
        problem_connectors: list[dict[str, Any]] = []

        for connector in connectors:
            status = connector.get('status', '').lower()

            if status in ('connected', 'working'):
                working_connectors += 1
            else:
                problem_connectors.append({
                    'id': connector.get('id'),
                    'name': connector.get('name'),
                    'status': status,
                    'type': connector.get('type'),
                    'last_sync': connector.get('last_sync'),
                })

        return {
            'total_connectors': total_connectors,
            'working_connectors': working_connectors,
            'problem_connectors': len(problem_connectors),
            'problem_connector_list': problem_connectors,
        }
