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
        scan_summary = scans.get('scan_summary', {})

        # Calculate totals from scan_summary
        total_completed = sum(s.get('completed_runs', 0) for s in scan_summary.values())
        total_failed = sum(s.get('failed_runs', 0) for s in scan_summary.values())

        scan_point = {
            'timestamp': timestamp,
            'total_scans': scans.get('unique_scans', 0),
            'total_launches': scans.get('total_launches', 0),
            'problem_scans': total_failed,
            'completed_scans': total_completed
        }

        # Extract scanner metrics
        scanners = current_data.get('scanners', {})
        scanner_point = {
            'timestamp': timestamp,
            'total_scanners': scanners.get('total_scanners', 0),
            'working_scanners': scanners.get('working_scanners', 0),
            'problem_scanners': scanners.get('problem_scanners', 0)
        }

        # Extract connector metrics
        connectors = current_data.get('connectors', {})
        connector_point = {
            'timestamp': timestamp,
            'total_connectors': connectors.get('total_connectors', 0),
            'working_connectors': connectors.get('working_connectors', 0),
            'problem_connectors': connectors.get('problem_connectors', 0)
        }

        # Extract user metrics
        users = current_data.get('users', {})
        user_point = {
            'timestamp': timestamp,
            'total_users': users.get('total_users', 0),
            'enabled_users': users.get('enabled_users', 0),
            'disabled_users': users.get('disabled_users', 0),
            'enabled_no_login_30_days': users.get('enabled_no_login_30_days', 0)
        }

        # Append to trends
        trends['authentication'].append(auth_point)
        trends['license'].append(license_point)
        trends['agents'].append(agent_point)
        trends['scans'].append(scan_point)

        # Add scanners key if it doesn't exist (backward compatibility)
        if 'scanners' not in trends:
            trends['scanners'] = []
        trends['scanners'].append(scanner_point)

        # Add connectors key if it doesn't exist (backward compatibility)
        if 'connectors' not in trends:
            trends['connectors'] = []
        trends['connectors'].append(connector_point)

        # Add users key if it doesn't exist (backward compatibility)
        if 'users' not in trends:
            trends['users'] = []
        trends['users'].append(user_point)

        self._save_trends(trends)
        logger.info(f"Saved trend data point for {timestamp}")

    def get_trends(self, metric_type=None, days=None, daily_aggregation=False):
        """
        Get trend data for charting.

        Args:
            metric_type: Optional filter ('authentication', 'license', 'agents', 'scans')
            days: Optional number of days to retrieve (default: all)
            daily_aggregation: If True, returns only the last data point per day

        Returns:
            Dict of trend data or list if metric_type specified
        """
        trends = self._load_trends()

        if daily_aggregation:
            trends = self._aggregate_by_day(trends)

        if metric_type:
            data = trends.get(metric_type, [])
        else:
            data = trends

        # TODO: Implement days filtering if needed
        return data

    def _aggregate_by_day(self, trends):
        """
        Aggregate trend data to have one data point per day (the last run of each day).

        Args:
            trends: Dict containing trend data for each metric type

        Returns:
            Dict with same structure but only one data point per day
        """
        aggregated = {}

        for metric_type, data_points in trends.items():
            # Group by date (YYYY-MM-DD)
            daily_data = {}

            for point in data_points:
                try:
                    timestamp = datetime.fromisoformat(point['timestamp'])
                    date_key = timestamp.strftime('%Y-%m-%d')

                    # Keep the latest timestamp for each date
                    if date_key not in daily_data or timestamp > datetime.fromisoformat(daily_data[date_key]['timestamp']):
                        daily_data[date_key] = point
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid data point in {metric_type}: {e}")
                    continue

            # Convert back to list, sorted by date
            aggregated[metric_type] = [
                daily_data[date_key]
                for date_key in sorted(daily_data.keys())
            ]

            logger.debug(f"Aggregated {metric_type}: {len(data_points)} points → {len(aggregated[metric_type])} daily points")

        return aggregated

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
            'scans': [],
            'scanners': [],
            'connectors': [],
            'users': []
        }

    def _save_trends(self, trends):
        """
        Save trends to file using atomic write operation.

        Args:
            trends: Trends data to save

        Raises:
            IOError: If file write fails
        """
        temp_file = self.trends_file.with_suffix('.tmp')

        try:
            # Write to temporary file first
            with open(temp_file, 'w') as f:
                json.dump(trends, f, indent=2)

            # Atomic rename
            temp_file.replace(self.trends_file)
            logger.debug(f"Successfully saved trends data to {self.trends_file}")

        except (IOError, OSError, TypeError, ValueError) as e:
            logger.error(f"Failed to save trends file: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise IOError(f"Failed to save trends data: {e}") from e

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
