from tenable.io import TenableIO
import logging

logger = logging.getLogger('tenable-healthcheck')


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
        """
        Get list of connectors via direct API call.

        Note: pytenable doesn't have a native connectors method, so we use
        the raw API endpoint. Returns empty list if unavailable.

        Returns:
            list: List of connector dictionaries, or empty list if unavailable
        """
        try:
            # pytenable may not have a direct connectors method, fall back to raw API
            response = self.tio.get('settings/connectors')
            connectors = response.get('connectors', [])
            logger.debug(f"Retrieved {len(connectors)} connectors from API")
            return connectors
        except AttributeError as e:
            # 'get' method doesn't exist in this pytenable version
            logger.warning(f"Connector API not available in this pytenable version: {e}")
            return []
        except Exception as e:
            # API error, permissions issue, or endpoint doesn't exist
            logger.warning(f"Unable to retrieve connectors: {type(e).__name__}: {str(e)}")
            return []
