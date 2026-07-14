"""Factory for creating LLM providers based on configuration."""
import logging
from typing import Any, Optional

from .base import LLMProvider
from .claude_cli import ClaudeCLIProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger('tenable-healthcheck')


def create_llm_provider(config: dict[str, Any]) -> Optional[LLMProvider]:
    """
    Create an LLM provider based on configuration.

    Args:
        config: Configuration dictionary with 'llm' section

    Returns:
        LLMProvider instance or None if AI analysis is disabled

    Configuration examples:
        # Claude CLI (default)
        {"llm": {"provider": "claude_cli"}}

        # OpenAI
        {"llm": {
            "provider": "openai",
            "api_key": "sk-...",
            "model": "gpt-4-turbo-preview"
        }}

        # Anthropic API
        {"llm": {
            "provider": "anthropic",
            "api_key": "sk-ant-...",
            "model": "claude-sonnet-4-20250514"
        }}

        # Ollama (local)
        {"llm": {
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434"
        }}

        # Disable AI analysis
        {"llm": {"enabled": false}}
    """
    llm_config = config.get('llm', {})

    # Check if AI analysis is disabled
    if not llm_config.get('enabled', True):
        logger.info("AI analysis is disabled in configuration")
        return None

    # Support legacy 'claude.use_cli' format
    if 'claude' in config and 'llm' not in config:
        logger.warning("Using legacy 'claude' config format. Consider updating to 'llm' format.")
        if config['claude'].get('use_cli', True):
            return ClaudeCLIProvider()
        return None

    provider_name = llm_config.get('provider', 'claude_cli')
    timeout = llm_config.get('timeout', 180)

    try:
        if provider_name == 'claude_cli':
            provider = ClaudeCLIProvider(timeout=timeout)
            if provider.is_available():
                logger.info(f"Using {provider.get_name()} for AI analysis")
                return provider
            else:
                logger.warning("Claude CLI not available. Install from: https://claude.ai/download")
                return None

        elif provider_name == 'openai':
            api_key = llm_config.get('api_key', '')
            model = llm_config.get('model', 'gpt-4-turbo-preview')

            if not api_key:
                logger.error("OpenAI API key not provided in configuration")
                return None

            provider = OpenAIProvider(api_key=api_key, model=model, timeout=timeout)
            if provider.is_available():
                logger.info(f"Using {provider.get_name()} for AI analysis")
                return provider
            else:
                logger.warning("OpenAI provider not available. Install with: pip install openai")
                return None

        elif provider_name == 'anthropic':
            api_key = llm_config.get('api_key', '')
            model = llm_config.get('model', 'claude-sonnet-4-20250514')

            if not api_key:
                logger.error("Anthropic API key not provided in configuration")
                return None

            provider = AnthropicProvider(api_key=api_key, model=model, timeout=timeout)
            if provider.is_available():
                logger.info(f"Using {provider.get_name()} for AI analysis")
                return provider
            else:
                logger.warning("Anthropic provider not available. Install with: pip install anthropic")
                return None

        elif provider_name == 'ollama':
            model = llm_config.get('model', 'llama2')
            base_url = llm_config.get('base_url', 'http://localhost:11434')

            provider = OllamaProvider(model=model, base_url=base_url, timeout=timeout)
            if provider.is_available():
                logger.info(f"Using {provider.get_name()} for AI analysis")
                return provider
            else:
                logger.warning(f"Ollama not available at {base_url}. Make sure it's running with: ollama serve")
                return None

        else:
            logger.error(f"Unknown LLM provider: {provider_name}")
            logger.info("Supported providers: claude_cli, openai, anthropic, ollama")
            return None

    except Exception as e:
        logger.error(f"Failed to create LLM provider '{provider_name}': {e}")
        return None
