class ConnectorCollector:
    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self):
        connectors = self.client.list_connectors()

        total_connectors = len(connectors)
        working_connectors = 0
        problem_connectors = []

        for connector in connectors:
            status = connector.get('status', '').lower()

            if status == 'connected' or status == 'working':
                working_connectors += 1
            else:
                problem_connectors.append({
                    'id': connector.get('id'),
                    'name': connector.get('name'),
                    'status': status,
                    'type': connector.get('type'),
                    'last_sync': connector.get('last_sync')
                })

        return {
            'total_connectors': total_connectors,
            'working_connectors': working_connectors,
            'problem_connectors': len(problem_connectors),
            'problem_connector_list': problem_connectors
        }
