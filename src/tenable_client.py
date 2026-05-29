from tenable.io import TenableIO


class TenableClient:
    def __init__(self, access_key, secret_key, base_url='https://cloud.tenable.com'):
        self.tio = TenableIO(access_key=access_key, secret_key=secret_key, url=base_url)

    def get_scans(self):
        scans = list(self.tio.scans.list())
        return {'scans': [self._scan_to_dict(scan) for scan in scans]}

    def _scan_to_dict(self, scan):
        return {
            'id': scan.get('id'),
            'name': scan.get('name'),
            'status': scan.get('status'),
            'last_modification_date': scan.get('last_modification_date'),
        }

    def get_scan_details(self, scan_id):
        return self.tio.scans.details(scan_id)

    def list_assets(self):
        # Use exports API to get full asset data including credential scan info
        # Filter out terminated and deleted assets
        assets = []
        for asset in self.tio.exports.assets():
            # Skip terminated assets
            if asset.get('terminated_at'):
                continue
            # Skip deleted assets
            if asset.get('deleted_at'):
                continue
            assets.append(asset)
        return assets

    def list_agents(self):
        # Get all agents across all scanners
        agents = []
        for agent in self.tio.agents.list():
            agents.append(agent)
        return agents

    def list_scanners(self):
        scanners = list(self.tio.scanners.list())
        return scanners

    def list_connectors(self):
        # Connectors might not be available in all Tenable environments
        try:
            # pytenable may not have a direct connectors method, fall back to raw API
            response = self.tio.get('settings/connectors')
            return response.get('connectors', [])
        except Exception:
            return []
