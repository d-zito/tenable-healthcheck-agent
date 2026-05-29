import subprocess
import json
import logging

logger = logging.getLogger('tenable-healthcheck')


class ClaudeAnalyzer:
    def __init__(self, use_cli=True):
        self.use_cli = use_cli

    def analyze_health_report(self, current_data, analysis_results):
        prompt = self._build_analysis_prompt(current_data, analysis_results)

        if self.use_cli:
            return self._analyze_via_cli(prompt)
        else:
            return {
                'summary': 'Claude API not configured. Install and configure Claude API keys to enable AI analysis.',
                'recommendations': []
            }

    def _build_analysis_prompt(self, current_data, analysis_results):
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
        prompt += json.dumps(current_data, indent=2)
        prompt += "\n\nComparison with Previous Run:\n"
        prompt += json.dumps(analysis_results, indent=2)

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

    def _analyze_via_cli(self, prompt):
        """
        Analyze health data using Claude CLI.

        Sends prompt via stdin to avoid command-line length limits.
        """
        try:
            logger.debug("Sending health data to Claude CLI for analysis")

            result = subprocess.run(
                ['claude', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.debug("Claude analysis completed successfully")
                # Try to parse JSON from the response
                output = result.stdout.strip()

                # Claude might wrap JSON in markdown code blocks
                if '```json' in output:
                    # Extract JSON from code block
                    start = output.find('```json') + 7
                    end = output.find('```', start)
                    output = output[start:end].strip()
                elif '```' in output:
                    # Generic code block
                    start = output.find('```') + 3
                    end = output.find('```', start)
                    output = output[start:end].strip()

                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, return the raw text as summary
                    logger.warning(f"Claude response was not valid JSON: {e}")
                    logger.debug(f"Claude raw output: {result.stdout}")
                    return {
                        'health_status': 'unknown',
                        'executive_summary': result.stdout,
                        'key_concerns': [],
                        'recommendations': [],
                        'trends': []
                    }
            else:
                logger.error(f"Claude CLI failed with exit code {result.returncode}")
                logger.debug(f"Claude stderr: {result.stderr}")
                return {
                    'error': 'Claude CLI failed',
                    'stderr': result.stderr
                }

        except subprocess.TimeoutExpired:
            logger.error("Claude analysis timed out after 60 seconds")
            return {
                'error': 'Claude analysis timed out'
            }
        except FileNotFoundError:
            logger.error("Claude CLI not found - is it installed?")
            return {
                'error': 'Claude CLI not found. Please install Claude Code CLI.',
                'help': 'Visit https://claude.ai/download to install Claude Code'
            }
        except Exception as e:
            logger.error(f"Unexpected error during Claude analysis: {e}", exc_info=True)
            return {
                'error': f'Unexpected error: {str(e)}'
            }
