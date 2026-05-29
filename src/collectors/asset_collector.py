from datetime import datetime, timedelta


class AssetCollector:
    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self):
        assets = self.client.list_assets()

        total_assets = len(assets)
        licensed_assets = 0
        auth_succeeded = 0
        auth_not_attempted = 0
        auth_failed = 0

        # Assets are licensed if last_licensed_scan_date is within past 90 days
        ninety_days_ago = datetime.now() - timedelta(days=90)

        for asset in assets:
            # Check if asset is licensed (scanned within past 90 days)
            last_licensed = asset.get('last_licensed_scan_date')
            if last_licensed:
                # Parse the date and check if within 90 days
                try:
                    licensed_date = datetime.fromisoformat(last_licensed.replace('Z', '+00:00'))
                    if licensed_date.replace(tzinfo=None) >= ninety_days_ago:
                        licensed_assets += 1

                        # Analyze authentication status for licensed assets
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

        # Calculate percentages
        auth_succeeded_pct = (auth_succeeded / licensed_assets * 100) if licensed_assets > 0 else 0
        auth_not_attempted_pct = (auth_not_attempted / licensed_assets * 100) if licensed_assets > 0 else 0
        auth_failed_pct = (auth_failed / licensed_assets * 100) if licensed_assets > 0 else 0

        return {
            'total_assets': total_assets,
            'licensed_assets': licensed_assets,
            'unlicensed_assets': total_assets - licensed_assets,
            'auth_succeeded': auth_succeeded,
            'auth_succeeded_percentage': round(auth_succeeded_pct, 2),
            'auth_not_attempted': auth_not_attempted,
            'auth_not_attempted_percentage': round(auth_not_attempted_pct, 2),
            'auth_failed': auth_failed,
            'auth_failed_percentage': round(auth_failed_pct, 2)
        }
