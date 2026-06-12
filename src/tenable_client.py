from __future__ import annotations

import functools
import logging
import time
from typing import Any

from tenable.io import TenableIO

logger = logging.getLogger('tenable-healthcheck')


def retry(max_attempts: int = 3, base_delay: float = 2.0, backoff_factor: float = 2.0):
    """Retry decorator with exponential backoff for transient API failures."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    # Don't retry on auth/permission errors
                    if any(code in error_str for code in ['401', '403', 'forbidden', 'unauthorized']):
                        raise
                    last_exception = e
                    if attempt < max_attempts:
                        delay = base_delay * (backoff_factor ** (attempt - 1))
                        logger.debug(f"Retrying {func.__name__} (attempt {attempt}/{max_attempts}) after {delay:.1f}s: {e}")
                        time.sleep(delay)
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator


class TenableClient:
    def __init__(self, access_key: str, secret_key: str, base_url: str = 'https://cloud.tenable.com') -> None:
        self.tio = TenableIO(access_key=access_key, secret_key=secret_key, url=base_url)

    @retry()
    def get_scans(self) -> dict[str, list[dict[str, Any]]]:
        scans = list(self.tio.scans.list())
        return {'scans': [self._scan_to_dict(scan) for scan in scans]}

    def _scan_to_dict(self, scan: dict[str, Any]) -> dict[str, Any]:
        return {
            'id': scan.get('id'),
            'name': scan.get('name'),
            'status': scan.get('status'),
            'last_modification_date': scan.get('last_modification_date'),
        }

    @retry()
    def get_scan_details(self, scan_id: int) -> Any:
        return self.tio.scans.details(scan_id)

    @retry()
    def list_assets(self) -> list[dict[str, Any]]:
        assets = []
        for asset in self.tio.exports.assets():
            if asset.get('terminated_at'):
                continue
            if asset.get('deleted_at'):
                continue
            assets.append(asset)
        return assets

    @retry()
    def list_agents(self) -> list[dict[str, Any]]:
        agents = []
        for agent in self.tio.agents.list():
            agents.append(agent)
        return agents

    @retry()
    def list_scanners(self) -> list[dict[str, Any]]:
        return list(self.tio.scanners.list())

    @retry()
    def list_users(self) -> list[dict[str, Any]]:
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
            raise

    @retry()
    def list_connectors(self) -> list[dict[str, Any]]:
        try:
            response = self.tio.get('settings/connectors')

            if isinstance(response, dict):
                connectors = response.get('connectors', [])
            else:
                connectors = response.json().get('connectors', [])

            logger.debug(f"Retrieved {len(connectors)} connectors from API")
            return connectors
        except AttributeError as e:
            logger.debug(f"Connector API response format unexpected: {e}")
            return []
        except (KeyError, TypeError, ValueError) as e:
            logger.debug(f"Could not parse connector data: {type(e).__name__}: {e}")
            return []
        except Exception as e:
            error_str = str(e).lower()
            if any(code in error_str for code in ['403', '404', 'forbidden', 'not found', 'unauthorized']):
                logger.info("Connectors endpoint not available (may require specific permissions or product tier)")
                return []
            raise
