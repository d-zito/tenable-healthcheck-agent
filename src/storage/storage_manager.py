import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


class StorageManager:
    def __init__(self, data_dir=None, retention_days=90):
        if data_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / "data" / "history"

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

    def save_run_data(self, data):
        # Use UTC for consistent timestamps across time zones
        now_utc = datetime.now(timezone.utc)
        timestamp = now_utc.strftime('%Y%m%d_%H%M%S')
        filename = f"healthcheck_{timestamp}.json"
        filepath = self.data_dir / filename

        # Handle both old format (just data) and new format (data + analysis)
        if isinstance(data, dict) and 'data' in data:
            # New format: data already contains 'data' and potentially 'claude_analysis'
            run_data = {
                'timestamp': now_utc.isoformat(),
                **data
            }
        else:
            # Old format: data is just the data dict
            run_data = {
                'timestamp': now_utc.isoformat(),
                'data': data
            }

        with open(filepath, 'w') as f:
            json.dump(run_data, f, indent=2)

        self._cleanup_old_data()
        return filepath

    def get_latest_run(self):
        files = sorted(self.data_dir.glob('healthcheck_*.json'))
        if not files:
            return None

        with open(files[-1], 'r') as f:
            return json.load(f)

    def get_previous_run(self):
        files = sorted(self.data_dir.glob('healthcheck_*.json'))
        if len(files) < 2:
            return None

        with open(files[-2], 'r') as f:
            return json.load(f)

    def get_all_runs(self, limit=None):
        files = sorted(self.data_dir.glob('healthcheck_*.json'))

        if limit:
            files = files[-limit:]

        runs = []
        for filepath in files:
            with open(filepath, 'r') as f:
                runs.append(json.load(f))

        return runs

    def _cleanup_old_data(self):
        # Use UTC for consistent date comparisons
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

        for filepath in self.data_dir.glob('healthcheck_*.json'):
            try:
                file_date_str = filepath.stem.replace('healthcheck_', '')
                file_date = datetime.strptime(file_date_str, '%Y%m%d_%H%M%S')

                if file_date < cutoff_date:
                    filepath.unlink()
            except (ValueError, OSError):
                continue
