"""OpenAI API provider implementation."""
import json
import logging
from typing import Any

from .base import LLMProvider

logger = logging.getLogger('tenable-healthcheck')


class OpenAIProvider(LLMProvider):
    """Provider that uses OpenAI API (GPT-4, etc)."""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", timeout: int = 180):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, timeout=self.timeout)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Install with: pip install openai"
                )
        return self._client

    def analyze(self, prompt: str) -> dict[str, Any]:
        """Analyze using OpenAI API."""
        try:
            logger.debug(f"Sending health data to OpenAI ({self.model}) for analysis")

            client = self._get_client()

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security analyst analyzing Tenable vulnerability management health data. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            output = response.choices[0].message.content.strip()

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
                logger.warning(f"OpenAI response was not valid JSON: {e}")
                logger.debug(f"OpenAI raw output: {output}")
                return {
                    'health_status': 'unknown',
                    'executive_summary': output,
                    'key_concerns': [],
                    'recommendations': [],
                    'trends': [],
                }

        except ImportError as e:
            logger.error(f"OpenAI library not available: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return {'error': f'OpenAI API error: {str(e)}'}

    def is_available(self) -> bool:
        """Check if OpenAI API is configured."""
        try:
            import openai
            return bool(self.api_key)
        except ImportError:
            return False

    def get_name(self) -> str:
        return f"OpenAI ({self.model})"
