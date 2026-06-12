from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ConfigLoader:
    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "config.json"

        self.config_path = Path(config_path)
        self.config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path}. "
                f"Please copy config.example.json to config.json and add your credentials."
            )

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def get_tenable_credentials(self) -> dict[str, str]:
        """
        Get Tenable credentials from environment variables or config file.
        Environment variables take precedence over config file values.

        Environment variables:
            TENABLE_ACCESS_KEY: Tenable API access key
            TENABLE_SECRET_KEY: Tenable API secret key
            TENABLE_BASE_URL: Tenable base URL (optional, defaults to https://cloud.tenable.com)

        Raises:
            ValueError: If required credentials are missing
        """
        config_creds = self.config.get('tenable', {})

        access_key = os.getenv('TENABLE_ACCESS_KEY', config_creds.get('access_key'))
        secret_key = os.getenv('TENABLE_SECRET_KEY', config_creds.get('secret_key'))

        if not access_key or access_key.startswith('YOUR_'):
            raise ValueError(
                "Tenable access key not found or not configured. Please set TENABLE_ACCESS_KEY environment variable "
                "or configure 'access_key' in config/config.json"
            )

        if not secret_key or secret_key.startswith('YOUR_'):
            raise ValueError(
                "Tenable secret key not found or not configured. Please set TENABLE_SECRET_KEY environment variable "
                "or configure 'secret_key' in config/config.json"
            )

        return {
            'access_key': access_key,
            'secret_key': secret_key,
            'base_url': os.getenv('TENABLE_BASE_URL', config_creds.get('base_url', 'https://cloud.tenable.com'))
        }

    def get_thresholds(self) -> dict[str, Any]:
        return self.config.get('thresholds', {})

    def get_data_retention_days(self) -> int:
        return self.config.get('data_retention_days', 90)

    def use_claude_cli(self) -> bool:
        return self.config.get('claude', {}).get('use_cli', True)
