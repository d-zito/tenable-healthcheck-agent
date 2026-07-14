# LLM Provider Configuration Examples

This document shows how to configure different LLM providers for AI-powered health analysis.

## Claude CLI (Default)

**No API key required** - uses local Claude Code CLI

```json
{
  "llm": {
    "enabled": true,
    "provider": "claude_cli",
    "timeout": 180
  }
}
```

**Install**: Download from https://claude.ai/download

## OpenAI (GPT-4)

**Requires API key** from https://platform.openai.com/api-keys

```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "api_key": "sk-proj-...",
    "model": "gpt-4-turbo-preview",
    "timeout": 180
  }
}
```

**Install dependency**:
```bash
pip install openai
```

**Supported models**:
- `gpt-4-turbo-preview` (recommended)
- `gpt-4`
- `gpt-3.5-turbo` (faster, cheaper)

## Anthropic API (Claude via API)

**Requires API key** from https://console.anthropic.com/

```json
{
  "llm": {
    "enabled": true,
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "model": "claude-sonnet-4-20250514",
    "timeout": 180
  }
}
```

**Install dependency**:
```bash
pip install anthropic
```

**Supported models**:
- `claude-sonnet-4-20250514` (recommended, balanced)
- `claude-opus-4-20250514` (most capable)
- `claude-haiku-4-20250514` (fastest, cheapest)

## Ollama (Local/Open Source)

**No API key required** - runs locally with open-source models

```json
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "model": "llama2",
    "base_url": "http://localhost:11434",
    "timeout": 180
  }
}
```

**Setup**:
1. Install Ollama: https://ollama.ai/download
2. Start server: `ollama serve`
3. Pull model: `ollama pull llama2`

**Supported models**:
- `llama2` (7B, good balance)
- `llama2:13b` (larger, more capable)
- `mistral` (fast, efficient)
- `mixtral` (most capable open model)
- `codellama` (code-focused)

## Disable AI Analysis

To run without AI analysis:

```json
{
  "llm": {
    "enabled": false
  }
}
```

## Environment Variables (Recommended for Production)

Instead of storing API keys in config files, use environment variables:

```bash
# OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-proj-...
export LLM_MODEL=gpt-4-turbo-preview

# Anthropic
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export LLM_MODEL=claude-sonnet-4-20250514

# Then in config.json, reference them
# (Config loader can be extended to support this)
```

## Cost Comparison

| Provider | Model | Cost (per 1M tokens) | Speed | Quality |
|----------|-------|---------------------|-------|---------|
| Claude CLI | Sonnet | Free* | Fast | Excellent |
| OpenAI | GPT-4 Turbo | $10 in / $30 out | Fast | Excellent |
| OpenAI | GPT-3.5 | $0.50 in / $1.50 out | Very Fast | Good |
| Anthropic | Claude Sonnet | $3 in / $15 out | Fast | Excellent |
| Anthropic | Claude Haiku | $0.25 in / $1.25 out | Very Fast | Good |
| Ollama | Llama 2 | Free | Slow | Good |

*Claude CLI requires a Claude subscription

## Recommendations

- **Development**: Use Claude CLI (free, no API key)
- **Production with budget**: Use OpenAI GPT-3.5 or Anthropic Haiku
- **Production best quality**: Use Anthropic Claude Sonnet or OpenAI GPT-4
- **Air-gapped/offline**: Use Ollama with local models
- **Cost-conscious**: Use Ollama (completely free)

## Troubleshooting

### Claude CLI not found
```
Install from: https://claude.ai/download
Test with: claude --version
```

### OpenAI authentication error
```
Check API key: https://platform.openai.com/api-keys
Ensure billing is set up
```

### Anthropic authentication error
```
Check API key: https://console.anthropic.com/
Verify API key starts with 'sk-ant-'
```

### Ollama connection refused
```
Start Ollama: ollama serve
Check it's running: curl http://localhost:11434/api/tags
Pull a model: ollama pull llama2
```

### Timeout errors
Increase timeout in config:
```json
{
  "llm": {
    "timeout": 300
  }
}
```
