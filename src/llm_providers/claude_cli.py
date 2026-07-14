"""Claude CLI provider implementation."""
import json
import logging
import subprocess
from typing import Any

from .base import LLMProvider

logger = logging.getLogger('tenable-healthcheck')


class ClaudeCLIProvider(LLMProvider):
    """Provider that uses the Claude CLI (claude command)."""

    def __init__(self, timeout: int = 180):
        self.timeout = timeout

    def analyze(self, prompt: str) -> dict[str, Any]:
        """Analyze using Claude CLI."""
        try:
            logger.debug("Sending health data to Claude CLI for analysis")

            result = subprocess.run(
                ['claude', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode == 0:
                logger.debug("Claude analysis completed successfully")
                output = result.stdout.strip()

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
                    logger.warning(f"Claude response was not valid JSON: {e}")
                    logger.debug(f"Claude raw output: {result.stdout}")
                    return {
                        'health_status': 'unknown',
                        'executive_summary': result.stdout,
                        'key_concerns': [],
                        'recommendations': [],
                        'trends': [],
                    }
            else:
                logger.error(f"Claude CLI failed with exit code {result.returncode}")
                logger.debug(f"Claude stderr: {result.stderr}")
                return {'error': 'Claude CLI failed', 'stderr': result.stderr}

        except subprocess.TimeoutExpired:
            logger.error(f"Claude analysis timed out after {self.timeout} seconds")
            return {'error': 'Claude analysis timed out'}
        except FileNotFoundError:
            logger.error("Claude CLI not found - is it installed?")
            return {
                'error': 'Claude CLI not found. Please install Claude Code CLI.',
                'help': 'Visit https://claude.ai/download to install Claude Code',
            }
        except Exception as e:
            logger.error(f"Unexpected error during Claude analysis: {e}", exc_info=True)
            return {'error': f'Unexpected error: {str(e)}'}

    def is_available(self) -> bool:
        """Check if Claude CLI is installed and accessible."""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_name(self) -> str:
        return "Claude CLI"
