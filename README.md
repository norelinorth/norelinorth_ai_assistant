# AI Assistant for ERPNext

Embedded AI Assistant inside ERPNext DocTypes with Langfuse observability.

## Overview

AI Assistant provides context-aware AI chat capabilities directly within your ERPNext documents. Configure once with AI Provider, and use AI assistance across Sales Orders, Purchase Orders, Invoices, and Journal Entries.

## Requirements

- Frappe Framework v15.0.0 or higher
- ERPNext v15.0.0 or higher (optional, for DocType integration)
- Python 3.10 or higher

## Features

### AI Assistant
- AI chat panel in Sales Orders, Purchase Orders, Invoices, and Journal Entries
- Context-aware responses using document data
- Session-based conversations with history
- Permission-based access control

### AI Provider (Shared Component)
- Single configuration point for all apps
- Supports OpenAI, Anthropic, Azure OpenAI
- Simple API for any Frappe app to use
- Langfuse observability for LLM tracing and monitoring

## Installation

```bash
bench get-app https://github.com/norelinorth/norelinorth_ai_assistant
bench --site yoursite.local install-app norelinorth_ai_assistant
```

## Configuration

### AI Provider Setup

1. Go to **AI Provider** (System Manager access required)
2. Configure:
   - **Provider**: OpenAI, Anthropic, or Azure OpenAI
   - **API Key**: Your provider API key
   - **Default Model**: e.g., gpt-4o-mini, claude-3-sonnet
   - **Is Active**: Check to enable

### Langfuse Observability (Optional)

Enable LLM tracing and monitoring:

1. In **AI Provider**, scroll to **Observability Settings**
2. Enable **Langfuse Observability**
3. Enter your Langfuse credentials:
   - Langfuse Public Key
   - Langfuse Secret Key
   - Langfuse Host (defaults to https://cloud.langfuse.com)

Benefits:
- Track all AI calls across your ERPNext instance
- Monitor token usage and costs
- Debug AI interactions with full traces
- No code changes required - automatic tracing

See [LANGFUSE_OBSERVABILITY.md](docs/LANGFUSE_OBSERVABILITY.md) for detailed setup.

## For Developers

### Using AI from Other Apps

```python
from norelinorth_ai_assistant.ai_provider_api import call_ai

response = call_ai(
    prompt="Analyze this data",
    context={"data": your_data}
)
```

### Architecture

```
norelinorth_ai_assistant/
├── AI Provider (Singles DocType)     # Shared configuration
├── ai_provider_api.py                # API functions for all apps
├── ai_observability.py               # Langfuse integration
├── AI Assistant Session              # Chat session management
└── doctype_hooks.py                  # DocType integration via hooks
```

## Permissions

| Role | Access |
|------|--------|
| AI Assistant Admin | Full access to AI Provider configuration |
| AI Assistant User | Use AI Assistant in supported DocTypes |
| System Manager | Configure AI Provider settings |

## Support

- **Issues**: [GitHub Issues](https://github.com/norelinorth/norelinorth_ai_assistant/issues)
- **Repository**: [GitHub](https://github.com/norelinorth/norelinorth_ai_assistant)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

