from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger('tenable-healthcheck')


class AssetCollector:
    """
    Collects asset data and authentication status from Tenable.

    Note: Tenable considers an asset "licensed" if it has been scanned within
    the past 90 days. This is how Tenable counts assets toward your license limit.
    Assets not scanned in 90 days don't count against your license.
    """

    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self):
        """
        Collect asset inventory and authentication statistics.

        Returns:
            dict: Asset counts and authentication success rates for recently scanned assets
        """
        assets = self.client.list_assets()
        logger.debug(f"Retrieved {len(assets)} total assets from Tenable")

        total_assets = len(assets)
        recently_scanned_assets = 0  # Assets scanned within 90 days (count toward license)
        auth_succeeded = 0
        auth_not_attempted = 0
        auth_failed = 0

        # Assets count toward license if scanned within past 90 days
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)

        for asset in assets:
            # Check if asset counts toward license (scanned within past 90 days)
            last_licensed = asset.get('last_licensed_scan_date')
            if last_licensed:
                # Parse the date and check if within 90 days
                try:
                    licensed_date = datetime.fromisoformat(last_licensed.replace('Z', '+00:00'))
                    if licensed_date >= ninety_days_ago:
                        recently_scanned_assets += 1

                        # Analyze authentication status for recently scanned assets only
                        last_auth_attempt = asset.get('last_authentication_attempt_date')
                        last_auth_success = asset.get('last_authenticated_scan_date')

                        if not last_auth_attempt:
                            # No authentication attempt
                            auth_not_attempted += 1
                        elif last_auth_success:
                            # Parse dates to compare
                            try:
                                attempt_date = datetime.fromisoformat(last_auth_attempt.replace('Z', '+00:00'))
                                success_date = datetime.fromisoformat(last_auth_success.replace('Z', '+00:00'))

                                if success_date >= attempt_date:
                                    # Authentication succeeded
                                    auth_succeeded += 1
                                else:
                                    # Latest attempt is newer than success, so it failed
                                    auth_failed += 1
                            except (ValueError, AttributeError):
                                # If we can't parse dates, assume failed
                                auth_failed += 1
                        else:
                            # Has attempt but no success = failed
                            auth_failed += 1
                except (ValueError, AttributeError):
                    # Skip assets with invalid date formats
                    pass

        # Calculate percentages based on recently scanned assets
        auth_succeeded_pct = (auth_succeeded / recently_scanned_assets * 100) if recently_scanned_assets > 0 else 0
        auth_not_attempted_pct = (auth_not_attempted / recently_scanned_assets * 100) if recently_scanned_assets > 0 else 0
        auth_failed_pct = (auth_failed / recently_scanned_assets * 100) if recently_scanned_assets > 0 else 0

        logger.info(f"Asset summary: {recently_scanned_assets}/{total_assets} scanned in past 90 days")
        logger.debug(f"Auth breakdown: {auth_succeeded} succeeded, {auth_not_attempted} not attempted, {auth_failed} failed")

        return {
            'total_assets': total_assets,
            'licensed_assets': recently_scanned_assets,  # Assets that count toward license
            'unlicensed_assets': total_assets - recently_scanned_assets,
            'auth_succeeded': auth_succeeded,
            'auth_succeeded_percentage': round(auth_succeeded_pct, 2),
            'auth_not_attempted': auth_not_attempted,
            'auth_not_attempted_percentage': round(auth_not_attempted_pct, 2),
            'auth_failed': auth_failed,
            'auth_failed_percentage': round(auth_failed_pct, 2)
        }
