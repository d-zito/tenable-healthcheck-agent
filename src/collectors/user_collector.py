from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from tenable_client import TenableClient

logger = logging.getLogger('tenable-healthcheck')

PERMISSION_ROLE_MAP: dict[int, str] = {
    16: 'Basic User',
    24: 'Scan Operator',
    32: 'Scan Manager',
    40: 'Administrator',
    64: 'System Administrator',
}


class UserCollector:
    """Collects user data from Tenable including status, login activity, and roles."""

    def __init__(self, tenable_client: TenableClient) -> None:
        self.client = tenable_client

    def collect(self) -> dict[str, Any]:
        """Collect user data including enabled/disabled status, login activity, and roles."""
        users = self.client.list_users()
        logger.debug(f"Retrieved {len(users)} users from Tenable")

        total_users = len(users)
        enabled_users = 0
        disabled_users = 0
        enabled_no_login_30_days = 0
        role_counts: dict[str, int] = {}

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        thirty_days_timestamp = int(thirty_days_ago.timestamp())

        users_no_login_list: list[dict[str, str]] = []

        for user in users:
            enabled = user.get('enabled', False)
            if enabled:
                enabled_users += 1
            else:
                disabled_users += 1

            if enabled:
                last_login = user.get('lastlogin') or user.get('last_login')

                if last_login is None or last_login == 0:
                    enabled_no_login_30_days += 1
                    users_no_login_list.append({
                        'username': user.get('username', 'Unknown'),
                        'name': user.get('name', 'Unknown'),
                        'email': user.get('email', 'N/A'),
                        'last_login': 'Never',
                    })
                elif last_login < thirty_days_timestamp:
                    enabled_no_login_30_days += 1
                    users_no_login_list.append({
                        'username': user.get('username', 'Unknown'),
                        'name': user.get('name', 'Unknown'),
                        'email': user.get('email', 'N/A'),
                        'last_login': datetime.fromtimestamp(last_login, tz=timezone.utc).strftime('%Y-%m-%d'),
                    })

            permissions = user.get('permissions', 0)
            role_name = self._map_permission_to_role(permissions)
            role_counts[role_name] = role_counts.get(role_name, 0) + 1

        users_no_login_list.sort(key=lambda x: (x['last_login'] != 'Never', x['last_login']))

        logger.info(f"User summary: {enabled_users} enabled, {disabled_users} disabled")
        logger.debug(f"Roles breakdown: {role_counts}")

        return {
            'total_users': total_users,
            'enabled_users': enabled_users,
            'disabled_users': disabled_users,
            'enabled_no_login_30_days': enabled_no_login_30_days,
            'enabled_no_login_list': users_no_login_list,
            'role_counts': role_counts,
        }

    @staticmethod
    def _map_permission_to_role(permissions: int) -> str:
        if permissions == 0:
            return 'Custom Role'
        return PERMISSION_ROLE_MAP.get(permissions, f'Unknown ({permissions})')
