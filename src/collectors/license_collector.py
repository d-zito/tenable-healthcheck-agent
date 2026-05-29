class LicenseCollector:
    def __init__(self, tenable_client):
        self.client = tenable_client

    def collect(self):
        # Count licensed assets from the asset inventory
        # Licensed assets are those that have been scanned and consume license capacity
        assets = self.client.list_assets()

        total_assets = len(assets)
        licensed_assets = 0

        # Assets that have been scanned (have last_licensed_scan_date) are consuming licenses
        for asset in assets:
            # Check for last_licensed_scan_date which indicates the asset consumed a license
            if asset.get('last_licensed_scan_date'):
                licensed_assets += 1

        return {
            'total_licensed_assets': licensed_assets,
            'total_assets': total_assets,
            'unlicensed_assets': total_assets - licensed_assets
        }
