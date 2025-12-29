# Langfuse Tracing and Filtering Guide

## Overview

The AI Assistant app now implements **standard Langfuse columns** for easy filtering and organization of AI traces. This allows you to distinguish between different apps and document types in the Langfuse dashboard.

## Implementation Details

### Source Parameter

All apps using the `call_ai()` function should now pass a `source` parameter to identify themselves:

```python
from ai_assistant.ai_provider_api import call_ai

# Example: AI Assistant
response = call_ai(
    prompt="What is the customer?",
    context=context_json,
    source="ai_assistant"  # Identifies the calling app
)

# Example: Journal Validation
response = call_ai(
    prompt="Analyze this journal entry",
    context=journal_context,
    source="journal_validation"
)
```

### Standard Langfuse Fields

The implementation automatically populates two standard Langfuse fields:

#### 1. **Tags** (Array Field)
- **First tag**: Source app identifier (from `source` parameter)
- **Second tag**: Document type (extracted from context if available)

**Examples:**
- `["ai_assistant", "Sales Order"]` - AI Assistant analyzing a Sales Order
- `["ai_assistant"]` - AI Assistant with no specific document context
- `["journal_validation", "Journal Entry"]` - Journal Validation analyzing a Journal Entry
- `["financial_asset_accounting", "Financial Asset"]` - Financial Asset app

#### 2. **Name** (Descriptive Trace Name)
- **Format**: `{Source App} - {DocType}` or just `{Source App}`
- Replaces generic "openai_completion" with descriptive names

**Examples:**
- `"Ai Assistant - Sales Order"`
- `"Ai Assistant"`
- `"Journal Validation - Journal Entry"`
- `"Financial Asset Accounting - Financial Asset"`

### Additional Metadata

The implementation also includes detailed metadata for advanced filtering:

```python
metadata = {
    "provider": "openai",
    "temperature": 0.7,
    "max_tokens": 2000,
    "has_context": true,
    "user": "Administrator",
    "source": "ai_assistant",
    "doctype": "Sales Order",        # If context provided
    "document_name": "SO-2025-0001"  # If context provided
}
```

## How to Filter in Langfuse Dashboard

### Basic Filtering

1. **Filter by App**
   - Go to: Langfuse → Traces
   - Filter: `tags CONTAINS "ai_assistant"`
   - Result: Shows only AI Assistant traces

2. **Filter by DocType**
   - Filter: `tags CONTAINS "Sales Order"`
   - Result: Shows all traces involving Sales Orders (from any app)

3. **Filter by Both**
   - Filter: `tags CONTAINS "ai_assistant" AND tags CONTAINS "Sales Order"`
   - Result: Shows only AI Assistant traces for Sales Orders

### Advanced Filtering

4. **Search by Name**
   - Search field: `"Ai Assistant - Sales Order"`
   - Result: Exact matches for this trace name

5. **Filter by Metadata**
   - Filter: `metadata.user = "Administrator"`
   - Filter: `metadata.doctype = "Journal Entry"`
   - Filter: `metadata.source = "journal_validation"`

6. **Combine Multiple Filters**
   ```
   tags CONTAINS "ai_assistant"
   AND metadata.user = "Administrator"
   AND metadata.has_context = true
   ```

## Code Implementation

### File: `apps/ai_assistant/ai_assistant/ai_provider_api.py`

**Lines 48-61**: Function signature with `source` parameter
```python
@frappe.whitelist()
def call_ai(prompt: str, context: Optional[str] = None, model: Optional[str] = None, source: Optional[str] = None) -> str:
    """
    Simple AI call interface for any app to use
    With automatic Langfuse tracing if enabled

    Args:
        prompt: The question or prompt
        context: Optional context (as JSON string or plain text)
        model: Optional model override
        source: Optional source app identifier (e.g., "ai_assistant", "ai_agent_framework")

    Returns:
        AI response as string
    """
```

**Lines 142-170**: Metadata extraction including doctype and document_name
```python
# Parse context to extract doctype information for better trace organization
trace_metadata = {
    "provider": prov.provider,
    "temperature": temperature,
    "max_tokens": max_tokens,
    "has_context": bool(context_data),
    "user": frappe.session.user,
    "source": source or "unknown"
}

# Add document context to metadata if available
if context_data:
    try:
        if isinstance(context_data, dict) and "scalar" in context_data:
            scalar = context_data.get("scalar", {})
            if "_doctype" in scalar:
                trace_metadata["doctype"] = scalar["_doctype"]
            if "_name" in scalar:
                trace_metadata["document_name"] = scalar["_name"]
    except Exception as e:
        frappe.logger().debug(f"Could not parse context for Langfuse metadata: {str(e)}")
```

**Lines 172-196**: Tags and descriptive names
```python
# Build tags for easy filtering in Langfuse
tags = []
if source:
    tags.append(source)  # e.g., "ai_assistant", "journal_validation"
if context_data and isinstance(context_data, dict) and "scalar" in context_data:
    if "_doctype" in context_data["scalar"]:
        tags.append(context_data["scalar"]["_doctype"])  # e.g., "Sales Order"

# Build descriptive name for the trace
trace_name = "AI Completion"
if source:
    trace_name = f"{source.replace('_', ' ').title()}"
if context_data and isinstance(context_data, dict) and "scalar" in context_data:
    doctype = context_data["scalar"].get("_doctype")
    if doctype:
        trace_name = f"{trace_name} - {doctype}"

# Use Langfuse context manager for tracing
with langfuse_client.start_as_current_generation(
    name=trace_name,
    model=model,
    input=messages,
    metadata=trace_metadata,
    tags=tags  # Standard Langfuse field for filtering
) as generation:
```

### File: `apps/ai_assistant/ai_assistant/api.py`

**Lines 75-89**: AI Assistant passes `source="ai_assistant"`
```python
# Call AI API using simplified provider API
try:
    # Build contextual prompt
    if context:
        full_prompt = f"""Context about {sess.target_doctype} '{sess.target_name}':
{system_context}

User Question: {prompt}

Please answer based on the provided context."""
        # Pass context separately for better Langfuse tracing
        reply = call_ai(prompt=full_prompt, context=system_context, source="ai_assistant")
    else:
        full_prompt = prompt
        reply = call_ai(prompt=full_prompt, source="ai_assistant")
```

## For Other Apps

If you have other apps using the `call_ai()` function (e.g., journal_validation, financial_asset_accounting), update them to pass the `source` parameter:

```python
# Before (no source)
reply = call_ai(prompt=my_prompt, context=my_context)

# After (with source)
reply = call_ai(prompt=my_prompt, context=my_context, source="journal_validation")
```

This will automatically create properly tagged and named traces in Langfuse.

## Benefits

1. **Easy Filtering**: Quickly find traces from specific apps or document types
2. **Debugging**: Identify which app is generating which AI calls
3. **Analytics**: Analyze usage patterns by app and document type
4. **Cost Tracking**: Track token usage per app using Langfuse analytics
5. **Quality Monitoring**: Monitor AI response quality for different use cases

## Troubleshooting

### Issue: Traces still show "openai_completion" as name

**Cause**: Source parameter not being passed

**Solution**: Ensure all `call_ai()` calls include `source` parameter:
```python
reply = call_ai(prompt=prompt, source="your_app_name")
```

### Issue: No doctype in tags

**Cause**: Context not being passed or context doesn't include `_doctype`

**Solution**:
1. Verify context is being passed to `call_ai()`
2. Ensure context includes `scalar._doctype` field
3. Check context extraction using `_extract_context()` function

### Issue: Duplicate traces in Langfuse

**Cause**: Previously fixed - was caused by manual `flush_langfuse()` calls

**Status**: ✅ Resolved - SDK now handles flushing automatically

## References

- Langfuse SDK Documentation: https://langfuse.com/docs/sdk/python
- Langfuse Tags Documentation: https://langfuse.com/docs/tracing/tags
- AI Provider API: `apps/ai_assistant/ai_assistant/ai_provider_api.py`
- AI Assistant API: `apps/ai_assistant/ai_assistant/api.py`
