import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger('tenable-healthcheck')


class TrendsManager:
    """
    Manages long-term trend data for health metrics.

    Stores lightweight time-series data in a single trends.json file for
    efficient charting and analysis. Unlike history files which have 90-day
    retention, trends can be kept longer-term (1 year+).
    """

    def __init__(self, trends_file=None):
        if trends_file is None:
            base_dir = Path(__file__).parent.parent.parent
            trends_file = base_dir / "data" / "trends.json"

        self.trends_file = Path(trends_file)
        self.trends_file.parent.mkdir(parents=True, exist_ok=True)

    def add_data_point(self, current_data):
        """
        Add a new data point from the current health check run.

        Args:
            current_data: Dict containing 'scans', 'assets', 'license', 'agents', etc.
        """
        trends = self._load_trends()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract authentication metrics
        assets = current_data.get('assets', {})
        auth_point = {
            'timestamp': timestamp,
            'total_assets': assets.get('total_assets', 0),
            'licensed_assets': assets.get('licensed_assets', 0),
            'auth_succeeded': assets.get('auth_succeeded', 0),
            'auth_succeeded_pct': assets.get('auth_succeeded_percentage', 0),
            'auth_failed': assets.get('auth_failed', 0),
            'auth_not_attempted': assets.get('auth_not_attempted', 0)
        }

        # Extract license metrics from assets (assets scanned in past 90 days)
        license_point = {
            'timestamp': timestamp,
            'total_licensed_assets': assets.get('licensed_assets', 0),
            'total_assets': assets.get('total_assets', 0),
            'unlicensed_assets': assets.get('unlicensed_assets', 0)
        }

        # Extract agent metrics
        agents = current_data.get('agents', {})
        agent_point = {
            'timestamp': timestamp,
            'total_agents': agents.get('total_agents', 0),
            'online_agents': agents.get('online_agents', 0),
            'offline_agents': agents.get('offline_agents', 0),
            'long_offline_agents': agents.get('long_offline_agents', 0)
        }

        # Extract scan metrics
        scans = current_data.get('scans', {})
        scan_point = {
            'timestamp': timestamp,
            'total_scans': scans.get('total_scans', 0),
            'problem_scans': len(scans.get('problem_scans', [])),
            'completed_scans': len(scans.get('completed_scans', []))
        }

        # Append to trends
        trends['authentication'].append(auth_point)
        trends['license'].append(license_point)
        trends['agents'].append(agent_point)
        trends['scans'].append(scan_point)

        self._save_trends(trends)
        logger.info(f"Saved trend data point for {timestamp}")

    def get_trends(self, metric_type=None, days=None):
        """
        Get trend data for charting.

        Args:
            metric_type: Optional filter ('authentication', 'license', 'agents', 'scans')
            days: Optional number of days to retrieve (default: all)

        Returns:
            Dict of trend data or list if metric_type specified
        """
        trends = self._load_trends()

        if metric_type:
            data = trends.get(metric_type, [])
        else:
            data = trends

        # TODO: Implement days filtering if needed
        return data

    def _load_trends(self):
        """Load existing trends or create new structure."""
        if self.trends_file.exists():
            try:
                with open(self.trends_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load trends file: {e}. Creating new trends.")

        # Return empty structure
        return {
            'authentication': [],
            'license': [],
            'agents': [],
            'scans': []
        }

    def _save_trends(self, trends):
        """Save trends to file."""
        try:
            with open(self.trends_file, 'w') as f:
                json.dump(trends, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save trends file: {e}")

    def cleanup_old_trends(self, days=365):
        """
        Remove trend data points older than specified days.

        Args:
            days: Number of days to keep (default: 365)
        """
        from datetime import timedelta

        trends = self._load_trends()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        modified = False

        for metric_type in trends.keys():
            original_count = len(trends[metric_type])
            trends[metric_type] = [
                point for point in trends[metric_type]
                if datetime.fromisoformat(point['timestamp']) >= cutoff_date
            ]
            removed = original_count - len(trends[metric_type])
            if removed > 0:
                logger.info(f"Removed {removed} old {metric_type} trend points (older than {days} days)")
                modified = True

        if modified:
            self._save_trends(trends)
