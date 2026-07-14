"""Base LLM provider interface."""
from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def analyze(self, prompt: str) -> dict[str, Any]:
        """
        Send a prompt to the LLM and return structured analysis.

        Args:
            prompt: The analysis prompt to send

        Returns:
            Dictionary with analysis results in the format:
            {
                'health_status': 'healthy|warning|critical',
                'executive_summary': 'Brief overview',
                'key_concerns': ['List of issues'],
                'recommendations': [
                    {
                        'priority': 'high|medium|low',
                        'issue': 'Issue description',
                        'action': 'Recommended action'
                    }
                ],
                'trends': ['Notable patterns']
            }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is properly configured and available."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the human-readable name of this provider."""
        pass
