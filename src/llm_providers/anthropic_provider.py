"""Anthropic API provider implementation."""
import json
import logging
from typing import Any

from .base import LLMProvider

logger = logging.getLogger('tenable-healthcheck')


class AnthropicProvider(LLMProvider):
    """Provider that uses Anthropic API directly."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", timeout: int = 180):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key, timeout=self.timeout)
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. Install with: pip install anthropic"
                )
        return self._client

    def analyze(self, prompt: str) -> dict[str, Any]:
        """Analyze using Anthropic API."""
        try:
            logger.debug(f"Sending health data to Anthropic API ({self.model}) for analysis")

            client = self._get_client()

            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            output = response.content[0].text.strip()

            # Extract JSON from markdown code blocks if present
            if '```json' in output:
                start = output.find('```json') + 7
                end = output.find('```', start)
                output = output[start:end].strip()
            elif '```' in output:
                start = output.find('```') + 3
                end = output.find('```', start)
                output = output[start:end].strip()

            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                logger.warning(f"Anthropic response was not valid JSON: {e}")
                logger.debug(f"Anthropic raw output: {output}")
                return {
                    'health_status': 'unknown',
                    'executive_summary': output,
                    'key_concerns': [],
                    'recommendations': [],
                    'trends': [],
                }

        except ImportError as e:
            logger.error(f"Anthropic library not available: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            return {'error': f'Anthropic API error: {str(e)}'}

    def is_available(self) -> bool:
        """Check if Anthropic API is configured."""
        try:
            import anthropic
            return bool(self.api_key)
        except ImportError:
            return False

    def get_name(self) -> str:
        return f"Anthropic API ({self.model})"
