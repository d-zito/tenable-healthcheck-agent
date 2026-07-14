"""Ollama provider implementation for local LLMs."""
import json
import logging
from typing import Any

from .base import LLMProvider

logger = logging.getLogger('tenable-healthcheck')


class OllamaProvider(LLMProvider):
    """Provider that uses Ollama for local LLM inference."""

    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434", timeout: int = 180):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def analyze(self, prompt: str) -> dict[str, Any]:
        """Analyze using Ollama."""
        try:
            import requests

            logger.debug(f"Sending health data to Ollama ({self.model}) for analysis")

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )

            if response.status_code == 200:
                output = response.json().get('response', '').strip()

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
                    logger.warning(f"Ollama response was not valid JSON: {e}")
                    logger.debug(f"Ollama raw output: {output}")
                    return {
                        'health_status': 'unknown',
                        'executive_summary': output,
                        'key_concerns': [],
                        'recommendations': [],
                        'trends': [],
                    }
            else:
                logger.error(f"Ollama request failed: {response.status_code}")
                return {'error': f'Ollama error: {response.text}'}

        except ImportError:
            logger.error("requests library not installed")
            return {'error': 'requests library required for Ollama. Install with: pip install requests'}
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to Ollama at {self.base_url}")
            return {
                'error': f'Could not connect to Ollama at {self.base_url}',
                'help': 'Make sure Ollama is running with: ollama serve'
            }
        except Exception as e:
            logger.error(f"Ollama error: {e}", exc_info=True)
            return {'error': f'Ollama error: {str(e)}'}

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_name(self) -> str:
        return f"Ollama ({self.model})"
