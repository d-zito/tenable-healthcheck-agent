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

    def list_users(self):
        """
        Get list of users using pytenable users.list() method.

        Returns:
            list: List of user dictionaries
        """
        try:
            users = list(self.tio.users.list())
            logger.debug(f"Retrieved {len(users)} users from API")
            return users
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Could not parse user data: {type(e).__name__}: {e}")
            return []
        except Exception as e:
            error_str = str(e).lower()
            if any(code in error_str for code in ['403', 'forbidden', 'unauthorized']):
                logger.info("Users endpoint not available (may require Administrator permissions)")
                return []
            logger.warning(f"Unexpected error retrieving users: {type(e).__name__}: {e}")
            return []

    def list_connectors(self):
        """
        Get list of connectors via direct API call.

        Note: pytenable doesn't have a native connectors method, so we use
        the raw API endpoint. Returns empty list if unavailable or unauthorized.

        Returns:
            list: List of connector dictionaries, or empty list if unavailable
        """
        try:
            # Use the TenableIO API directly - response is already parsed to dict
            response = self.tio.get('settings/connectors')

            # Check if response is a dict or needs parsing
            if isinstance(response, dict):
                connectors = response.get('connectors', [])
            else:
                # If it's a Response object, parse it
                connectors = response.json().get('connectors', [])

            logger.debug(f"Retrieved {len(connectors)} connectors from API")
            return connectors
        except AttributeError as e:
            # Response object doesn't have expected methods
            logger.debug(f"Connector API response format unexpected: {e}")
            return []
        except (KeyError, TypeError, ValueError) as e:
            # Data parsing issues
            logger.debug(f"Could not parse connector data: {type(e).__name__}: {e}")
            return []
        except Exception as e:
            # Check if it's a known permission/availability issue
            error_str = str(e).lower()
            if any(code in error_str for code in ['403', '404', 'forbidden', 'not found', 'unauthorized']):
                logger.info("Connectors endpoint not available (may require specific permissions or product tier)")
                return []
            # Unexpected error - log for investigation but don't fail the whole run
            logger.warning(f"Unexpected error retrieving connectors: {type(e).__name__}: {e}")
            return []
