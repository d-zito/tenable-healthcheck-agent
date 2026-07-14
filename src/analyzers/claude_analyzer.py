from __future__ import annotations

import json
import logging
from typing import Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_providers import create_llm_provider, LLMProvider

logger = logging.getLogger('tenable-healthcheck')


class ClaudeAnalyzer:
    """
    AI-powered health analysis using configurable LLM providers.

    Despite the class name 'ClaudeAnalyzer', this now supports multiple LLM providers
    including Claude CLI, OpenAI, Anthropic API, and Ollama.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize analyzer with LLM provider from config.

        Args:
            config: Full configuration dictionary with 'llm' section
        """
        self.provider: Optional[LLMProvider] = create_llm_provider(config)

    def analyze_health_report(self, current_data: dict[str, Any], analysis_results: dict[str, Any]) -> dict[str, Any]:
        prompt = self._build_analysis_prompt(current_data, analysis_results)

        if self.provider:
            logger.info(f"Running AI analysis with {self.provider.get_name()}")
            return self.provider.analyze(prompt)

        return {
            'health_status': 'unknown',
            'executive_summary': 'AI analysis is disabled or no LLM provider configured.',
            'key_concerns': [],
            'recommendations': [],
            'trends': [],
        }

    def _summarize_current_data(self, current_data: dict[str, Any]) -> dict[str, Any]:
        """Reduce current_data to counts and samples to avoid oversized payloads."""
        summary: dict[str, Any] = {}

        for key, value in current_data.items():
            if not isinstance(value, dict):
                summary[key] = value
                continue

            section: dict[str, Any] = {}
            for field, val in value.items():
                # Keep scalar counts/rates/timestamps directly
                if not isinstance(val, list):
                    section[field] = val
                else:
                    # Summarize lists: count + first 5 items
                    section[f"{field}_count"] = len(val)
                    if val:
                        section[f"{field}_sample"] = val[:5]
            summary[key] = section

        return summary

    def _summarize_analysis_results(self, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """Reduce analysis_results to deltas and flags only."""
        summary: dict[str, Any] = {}

        for key, value in analysis_results.items():
            if not isinstance(value, dict):
                summary[key] = value
                continue

            section: dict[str, Any] = {}
            for field, val in value.items():
                if isinstance(val, list):
                    section[f"{field}_count"] = len(val)
                    if val:
                        section[f"{field}_sample"] = val[:5]
                else:
                    section[field] = val
            summary[key] = section

        return summary

    def _build_analysis_prompt(self, current_data: dict[str, Any], analysis_results: dict[str, Any]) -> str:
        prompt = """You are analyzing a Tenable One health check report. Please provide:

1. A brief executive summary of the overall health status
2. Key concerns or issues that require immediate attention
3. Specific recommendations for addressing any problems
4. Trends or patterns that should be monitored

IMPORTANT GUIDELINES:
- Scanners: ONLY flag as an issue if there are problem_scanners > 0 or offline scanners
- Agents: ONLY flag as an issue if there are offline_agents > 0 or long_offline_agents > 0
- If all scanners are working and all agents are online, this is HEALTHY - do not mention as a concern
- Scans: Flag aborted, stopped, or canceled scans as issues
- Authentication: Flag significant drops in credential scan success rate
- License: Flag if approaching license limits or unexpected changes

Current Data:
"""
        prompt += json.dumps(self._summarize_current_data(current_data), indent=2)
        prompt += "\n\nComparison with Previous Run:\n"
        prompt += json.dumps(self._summarize_analysis_results(analysis_results), indent=2)

        prompt += """

Please provide your analysis in the following JSON format:
{
  "health_status": "healthy|warning|critical",
  "executive_summary": "Brief overview of findings",
  "key_concerns": ["List of major issues - ONLY actual problems, not healthy systems"],
  "recommendations": [
    {
      "priority": "high|medium|low",
      "issue": "Description of the issue",
      "action": "Recommended action to take"
    }
  ],
  "trends": ["Notable trends or patterns"]
}

Remember: If scanners are all working and agents are all online, these are positives, not concerns.
"""
        return prompt
