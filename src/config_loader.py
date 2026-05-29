import json
import os
from pathlib import Path


class ConfigLoader:
    def __init__(self, config_path=None):
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path}. "
                f"Please copy config.example.json to config.json and add your credentials."
            )

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def get_tenable_credentials(self):
        return {
            'access_key': self.config['tenable']['access_key'],
            'secret_key': self.config['tenable']['secret_key'],
            'base_url': self.config['tenable'].get('base_url', 'https://cloud.tenable.com')
        }

    def get_thresholds(self):
        return self.config.get('thresholds', {})

    def get_data_retention_days(self):
        return self.config.get('data_retention_days', 90)

    def use_claude_cli(self):
        return self.config.get('claude', {}).get('use_cli', True)
