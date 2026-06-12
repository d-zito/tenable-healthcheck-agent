from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger('tenable-healthcheck')


class StorageManager:
    def __init__(self, data_dir: str | Path | None = None, retention_days: int = 90) -> None:
        if data_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / "data" / "history"

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

    def save_run_data(self, data: dict[str, Any]) -> Path:
        """Save run data to JSON file using atomic write operation."""
        now_utc = datetime.now(timezone.utc)
        timestamp = now_utc.strftime('%Y%m%d_%H%M%S')
        filename = f"healthcheck_{timestamp}.json"
        filepath = self.data_dir / filename
        temp_filepath = filepath.with_suffix('.tmp')

        if isinstance(data, dict) and 'data' in data:
            run_data = {'timestamp': now_utc.isoformat(), **data}
        else:
            run_data = {'timestamp': now_utc.isoformat(), 'data': data}

        try:
            with open(temp_filepath, 'w') as f:
                json.dump(run_data, f, indent=2)
            temp_filepath.replace(filepath)
            logger.debug(f"Successfully saved run data to {filepath}")
        except (IOError, OSError, TypeError, ValueError) as e:
            logger.error(f"Failed to save run data to {filepath}: {e}")
            if temp_filepath.exists():
                try:
                    temp_filepath.unlink()
                except OSError:
                    pass
            raise IOError(f"Failed to save health check data: {e}") from e

        self._cleanup_old_data()
        return filepath

    def get_latest_run(self) -> dict[str, Any] | None:
        files = sorted(self.data_dir.glob('healthcheck_*.json'))
        if not files:
            return None
        with open(files[-1], 'r') as f:
            return json.load(f)

    def get_previous_run(self) -> dict[str, Any] | None:
        files = sorted(self.data_dir.glob('healthcheck_*.json'))
        if len(files) < 2:
            return None
        with open(files[-2], 'r') as f:
            return json.load(f)

    def get_all_runs(self, limit: int | None = None) -> list[dict[str, Any]]:
        files = sorted(self.data_dir.glob('healthcheck_*.json'))
        if limit:
            files = files[-limit:]

        runs: list[dict[str, Any]] = []
        for filepath in files:
            with open(filepath, 'r') as f:
                runs.append(json.load(f))
        return runs

    def _cleanup_old_data(self) -> None:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

        for filepath in self.data_dir.glob('healthcheck_*.json'):
            try:
                file_date_str = filepath.stem.replace('healthcheck_', '')
                file_date = datetime.strptime(file_date_str, '%Y%m%d_%H%M%S').replace(tzinfo=timezone.utc)
                if file_date < cutoff_date:
                    filepath.unlink()
            except (ValueError, OSError):
                continue
