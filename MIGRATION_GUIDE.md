# Migration Guide: LLM-Agnostic Updates

## What Changed

The project now supports multiple LLM providers instead of being Claude-specific.

## Breaking Changes

### Configuration Format

**Old format** (still supported with deprecation warning):
```json
{
  "claude": {
    "use_cli": true
  }
}
```

**New format** (recommended):
```json
{
  "llm": {
    "enabled": true,
    "provider": "claude_cli"
  }
}
```

## Migration Steps

### For Existing Users

1. **Update your `config/config.json`:**

   Replace:
   ```json
   "claude": {
     "use_cli": true
   }
   ```
   
   With:
   ```json
   "llm": {
     "enabled": true,
     "provider": "claude_cli"
   }
   ```

2. **No code changes needed** - The tool still works the same way

### For New Users

1. Copy `config/config.example.json` to `config/config.json`
2. Choose your LLM provider (see [LLM Configuration Guide](docs/LLM_CONFIGURATION.md))
3. Run normally with `python3 src/main.py`

## Available Providers

| Provider | Best For | Requires |
|----------|----------|----------|
| `claude_cli` | Development, Claude Code users | Claude Code CLI installed |
| `openai` | Production with GPT-4 | OpenAI API key + `pip install openai` |
| `anthropic` | Production with Claude | Anthropic API key + `pip install anthropic` |
| `ollama` | Air-gapped/offline environments | Ollama installed locally |
| `enabled: false` | No LLM access | Nothing |

## Backward Compatibility

The old `"claude": {"use_cli": true}` format still works but shows a deprecation warning. It will be removed in a future version.

## New Features

- Support for OpenAI GPT-4
- Support for Anthropic Claude API
- Support for Ollama (local open-source models)
- Graceful degradation when no LLM is available
- Better error messages for missing dependencies

## Questions?

See the full [LLM Configuration Guide](docs/LLM_CONFIGURATION.md) for detailed setup instructions.
