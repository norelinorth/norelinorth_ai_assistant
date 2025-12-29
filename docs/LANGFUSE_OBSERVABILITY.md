# Langfuse Observability Integration

## Overview

The ai_assistant app now includes integrated **Langfuse observability** for LLM tracing and monitoring. This allows you to track all AI calls across your entire ERPNext installation from a single, centralized dashboard.

## Why Langfuse in ai_assistant?

Following the same pattern as AI Provider configuration, Langfuse observability is centralized in the `ai_assistant` app:

✅ **Single Source of Truth**: One Langfuse configuration for entire ERPNext instance
✅ **Zero-Friction Integration**: All apps using `call_ai()` automatically get tracing
✅ **No Code Changes Required**: Existing apps work without modification
✅ **Unified Dashboard**: All AI calls traced to one Langfuse project
✅ **Optional**: Enable/disable with a checkbox - no impact when disabled

## Features

- **Automatic Tracing**: Every `call_ai()` call automatically traced to Langfuse
- **Token Usage Tracking**: Prompt tokens, completion tokens, and total usage captured
- **User Context**: Each trace includes Frappe user and session information
- **Model Metadata**: Provider, model, temperature, and other parameters logged
- **Error Handling**: Graceful fallback if Langfuse is unavailable
- **No Performance Impact**: Tracing happens asynchronously

## Setup

### 1. Get Langfuse Credentials

1. Sign up at [https://cloud.langfuse.com](https://cloud.langfuse.com) (or use self-hosted)
2. Create a new project
3. Copy your **Public Key** and **Secret Key** from project settings

### 2. Configure in ERPNext

1. Go to **AI Provider** (Single DocType)
2. Scroll to **Observability Settings** section
3. Enable **Langfuse Observability** checkbox
4. Enter **Langfuse Public Key**
5. Enter **Langfuse Secret Key**
6. Set **Langfuse Host** (defaults to `https://cloud.langfuse.com`)
7. Save

### 3. Verify Configuration

Run this in bench console:

```python
from ai_assistant.ai_observability import validate_langfuse_config
result = validate_langfuse_config()
print(result)
```

Expected output when configured:
```python
{
    "enabled": True,
    "configured": True,
    "status": "active",
    "message": "Langfuse observability is active",
    "host": "https://cloud.langfuse.com"
}
```

## Usage

### For App Developers

**No code changes required!** If your app already uses the AI Provider API, tracing is automatic:

```python
# Your existing code - no changes needed!
from ai_assistant.ai_provider_api import call_ai

# This call is automatically traced to Langfuse if enabled
response = call_ai(
    prompt="Analyze this journal entry",
    context=json.dumps({"amount": 1000, "account": "Cash"})
)
```

### What Gets Traced

Each AI call creates a trace in Langfuse with:

- **Trace Name**: `ai_call`
- **User ID**: Current Frappe user (e.g., `administrator@example.com`)
- **Session ID**: Frappe session ID
- **Model**: OpenAI model used (e.g., `gpt-4o-mini`)
- **Input**: Complete message array sent to OpenAI
- **Output**: AI response text
- **Metadata**:
  - Provider (e.g., `OpenAI`)
  - Model name
  - Temperature (0.7)
  - Max tokens (2000)
  - Has context (boolean)
- **Usage**:
  - Prompt tokens
  - Completion tokens
  - Total tokens

### Example Trace in Langfuse

```
Trace: ai_call
├── User: administrator@example.com
├── Session: abc123xyz
├── Model: gpt-4o-mini
├── Input: [
│     {"role": "system", "content": "You are a helpful assistant..."},
│     {"role": "user", "content": "Analyze this journal entry"}
│   ]
├── Output: "This journal entry shows..."
└── Usage: 45 prompt tokens, 120 completion tokens, 165 total
```

## Architecture

### Components

```
ai_assistant/
├── ai_provider_api.py           # Modified to add Langfuse tracing
├── ai_observability.py          # NEW - Langfuse utilities
└── doctype/
    └── ai_provider/
        └── ai_provider.json     # Extended with Langfuse fields
```

### How It Works

1. **Configuration**: Langfuse credentials stored in AI Provider Single DocType
2. **Client Initialization**: `get_langfuse_client()` creates singleton client
3. **Automatic Tracing**: `call_ai()` wraps OpenAI calls with Langfuse traces
4. **Token Capture**: OpenAI usage data automatically logged
5. **Async Flush**: Events sent to Langfuse asynchronously

### Security

- **Credentials**: Langfuse Secret Key stored using Frappe's encrypted Password field
- **Permissions**: Same permission model as AI Provider (System Manager, AI Assistant Admin)
- **No Exposure**: Credentials never exposed via API or client-side
- **Fail-Safe**: If Langfuse fails, AI calls continue normally (logged to Error Log)

## API Reference

### `validate_langfuse_config()`

Validate Langfuse configuration and status.

```python
from ai_assistant.ai_observability import validate_langfuse_config

result = validate_langfuse_config()
# Returns: {"enabled": bool, "configured": bool, "status": str, "message": str}
```

**Statuses:**
- `active` - Langfuse configured and working
- `disabled` - Langfuse not enabled
- `incomplete` - Missing credentials
- `error` - Configuration error

### `get_langfuse_client()`

Get Langfuse client instance (for advanced use cases).

```python
from ai_assistant.ai_observability import get_langfuse_client

client = get_langfuse_client()
if client:
    # Custom tracing logic
    trace = client.trace(name="custom_operation")
```

### `create_trace()`

Create a custom trace (for advanced use cases).

```python
from ai_assistant.ai_observability import create_trace

trace = create_trace(
    name="custom_workflow",
    metadata={"step": "validation", "doctype": "Journal Entry"}
)
```

### `flush_langfuse()`

Manually flush pending Langfuse events.

```python
from ai_assistant.ai_observability import flush_langfuse

flush_langfuse()  # Ensure all events sent before process exit
```

## Multi-App Usage

### Example: Journal Validation App

```python
# journal_validation/journal_validation/api.py

from ai_assistant.ai_provider_api import call_ai
import json

@frappe.whitelist()
def validate_journal_entry(journal_entry_name):
    """Validate journal entry using AI - automatically traced to Langfuse"""

    doc = frappe.get_doc("Journal Entry", journal_entry_name)

    # Prepare context
    context = {
        "doctype": "Journal Entry",
        "name": doc.name,
        "total_debit": doc.total_debit,
        "total_credit": doc.total_credit,
        "accounts": [{"account": row.account, "debit": row.debit, "credit": row.credit}
                     for row in doc.accounts]
    }

    # Call AI - automatically traced to Langfuse!
    response = call_ai(
        prompt="Validate this journal entry for accounting compliance",
        context=json.dumps(context)
    )

    return response
```

**Result**: This call appears in Langfuse dashboard with:
- User who triggered validation
- Full journal entry context
- AI response
- Token usage
- All without any Langfuse-specific code!

## Dashboard Usage

### Viewing Traces

1. Log into Langfuse dashboard
2. Navigate to **Traces**
3. Filter by:
   - User ID (Frappe user email)
   - Session ID
   - Date range
   - Model

### Analyzing Usage

1. Navigate to **Analytics**
2. View:
   - Total tokens used
   - Cost estimates
   - Model distribution
   - User activity
   - Error rates

### Debugging

1. Click on any trace to see:
   - Full input/output
   - Timing information
   - Token breakdown
   - Metadata
   - Errors (if any)

## Performance Considerations

### Overhead

- **Minimal**: Langfuse SDK uses async event batching
- **No Blocking**: AI calls don't wait for Langfuse
- **Cached Client**: Singleton pattern avoids repeated initialization

### When to Disable

Disable Langfuse if:
- You don't need observability
- You're in a highly resource-constrained environment
- You want to reduce external dependencies

**How to Disable**: Simply uncheck "Enable Langfuse Observability" in AI Provider settings.

## Troubleshooting

### Issue: "Langfuse credentials incomplete"

**Solution**: Ensure both Public Key and Secret Key are configured in AI Provider.

### Issue: Traces not appearing in dashboard

**Checks**:
1. Verify credentials are correct
2. Check Error Log for Langfuse errors: `Desk → Tools → Error Log`
3. Ensure Langfuse Host is correct
4. Test network connectivity to Langfuse host

### Issue: AI calls failing with Langfuse enabled

**Solution**: Langfuse failures should not affect AI calls. Check Error Log for details. If persisting, temporarily disable Langfuse to isolate the issue.

### Issue: Token usage not captured

**Cause**: Token usage comes from OpenAI API response. If using a different provider or custom endpoint, usage data may not be available.

## Self-Hosted Langfuse

To use self-hosted Langfuse:

1. Deploy Langfuse following [official docs](https://langfuse.com/docs/deployment/self-host)
2. In AI Provider settings, set **Langfuse Host** to your instance URL
   - Example: `https://langfuse.yourcompany.com`
3. Use credentials from your self-hosted instance

## Best Practices

### 1. Use Descriptive Context

Include meaningful context in AI calls for better trace debugging:

```python
# Good - detailed context
context = {
    "doctype": "Journal Entry",
    "name": doc.name,
    "company": doc.company,
    "posting_date": str(doc.posting_date),
    "purpose": "validation"
}

# Bad - minimal context
context = {"data": doc.as_dict()}
```

### 2. Monitor Token Usage

Regularly check Langfuse analytics to:
- Identify high-usage features
- Optimize prompts
- Control costs

### 3. Set Up Alerts

Configure Langfuse alerts for:
- High error rates
- Unusual token usage
- Latency spikes

### 4. Use Tags

Add custom tags via metadata for filtering:

```python
from ai_assistant.ai_observability import create_trace

trace = create_trace(
    name="journal_validation",
    metadata={
        "feature": "accounting",
        "risk_level": "high",
        "environment": "production"
    }
)
```

## Roadmap

Future enhancements planned:
- [ ] Support for other LLM providers (Anthropic, Azure OpenAI)
- [ ] Custom trace names per app/feature
- [ ] Langfuse experiments integration
- [ ] Prompt versioning and management
- [ ] Cost tracking and budgets

## Support

For issues or questions:
1. Check Error Log in ERPNext: `Desk → Tools → Error Log`
2. Test configuration: `validate_langfuse_config()`
3. Review Langfuse documentation: [https://langfuse.com/docs](https://langfuse.com/docs)
4. Open an issue in the ai_assistant repository

## License

This integration is part of the ai_assistant app and follows the same MIT license.
