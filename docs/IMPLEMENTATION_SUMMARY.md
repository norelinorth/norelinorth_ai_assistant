# Langfuse Tags Implementation - Summary

## What Was Implemented

This implementation adds **standard Langfuse columns** (tags and descriptive names) to make AI traces from different apps and document types easily distinguishable in the Langfuse dashboard.

## Changes Made

### 1. ai_provider_api.py (ai_assistant/ai_provider_api.py)

**Line 48**: Added `source` parameter to function signature
```python
def call_ai(prompt: str, context: Optional[str] = None, model: Optional[str] = None, source: Optional[str] = None) -> str:
```

**Lines 142-170**: Enhanced metadata extraction
- Added `source` to metadata
- Extract `_doctype` and `_name` from context
- Properly handle different context formats

**Lines 172-196**: Implemented Langfuse tags and descriptive names
```python
# Build tags for easy filtering
tags = []
if source:
    tags.append(source)  # e.g., "ai_assistant"
if context_data and "_doctype" in context_data.get("scalar", {}):
    tags.append(context_data["scalar"]["_doctype"])  # e.g., "Sales Order"

# Build descriptive trace name
trace_name = "AI Completion"
if source:
    trace_name = f"{source.replace('_', ' ').title()}"
if doctype:
    trace_name = f"{trace_name} - {doctype}"

# Pass to Langfuse
with langfuse_client.start_as_current_generation(
    name=trace_name,
    tags=tags,
    ...
) as generation:
```

### 2. api.py (ai_assistant/api.py)

**Lines 86 and 89**: Added `source="ai_assistant"` parameter to all call_ai() calls
```python
# With context
reply = call_ai(prompt=full_prompt, context=system_context, source="ai_assistant")

# Without context
reply = call_ai(prompt=full_prompt, source="ai_assistant")
```

## How It Works

### Trace Attributes

When you use AI Assistant to analyze a Sales Order, the Langfuse trace will have:

**Tags**: `["ai_assistant", "Sales Order"]`
- First tag identifies the app
- Second tag identifies the document type

**Name**: `"Ai Assistant - Sales Order"`
- Descriptive name instead of generic "openai_completion"
- Format: "{Source App} - {DocType}"

**Metadata**:
```json
{
  "provider": "openai",
  "source": "ai_assistant",
  "doctype": "Sales Order",
  "document_name": "SO-2025-0001",
  "user": "Administrator",
  "has_context": true
}
```

### Example Traces

| Action | Tags | Name |
|--------|------|------|
| AI Assistant on Sales Order | `["ai_assistant", "Sales Order"]` | `"Ai Assistant - Sales Order"` |
| AI Assistant general question | `["ai_assistant"]` | `"Ai Assistant"` |
| Journal Validation | `["journal_validation", "Journal Entry"]` | `"Journal Validation - Journal Entry"` |

## Benefits

1. **Easy Filtering in Langfuse**
   - Filter by app: `tags CONTAINS "ai_assistant"`
   - Filter by doctype: `tags CONTAINS "Sales Order"`
   - Combine: Both app AND doctype

2. **Clear Trace Identification**
   - No more generic "openai_completion" names
   - Instantly see what each trace is analyzing

3. **Better Debugging**
   - Quickly identify which app generated which call
   - Trace document-specific AI interactions

4. **Usage Analytics**
   - Track token usage by app
   - Analyze patterns by document type
   - Monitor quality by use case

## Testing

To test the implementation:

1. **Use AI Assistant on a Sales Order**
   - Open any Sales Order in ERPNext
   - Click the AI Assistant icon
   - Ask a question about the order
   - Check Langfuse dashboard

2. **Verify Trace Attributes**
   - Tags should show: `["ai_assistant", "Sales Order"]`
   - Name should show: `"Ai Assistant - Sales Order"`
   - Metadata should include doctype and document_name

3. **Test Filtering**
   - In Langfuse, filter by: `tags CONTAINS "ai_assistant"`
   - Should show only AI Assistant traces
   - Filter by: `tags CONTAINS "Sales Order"`
   - Should show only Sales Order traces

## For Other Apps

If you have other apps using the AI system (like journal_validation, financial_asset_accounting), update them to pass the `source` parameter:

```python
# Before
response = call_ai(prompt=my_prompt, context=my_context)

# After
response = call_ai(
    prompt=my_prompt,
    context=my_context,
    source="journal_validation"  # or your app name
)
```

This will automatically:
- Tag traces with your app name
- Create descriptive trace names
- Enable filtering by your app in Langfuse

## Previous Issues Resolved

This implementation also resolves several previous issues:

1. ✅ **Tracing not working** - Fixed missing context parameter
2. ✅ **All traces look identical** - Added doctype/document_name metadata
3. ✅ **Duplicate traces** - Removed manual flush_langfuse() calls
4. ✅ **Cannot distinguish different apps** - Implemented tags and names

## Files Modified

- `apps/ai_assistant/ai_assistant/ai_provider_api.py` (lines 48, 142-196)
- `apps/ai_assistant/ai_assistant/api.py` (lines 86, 89)

## Documentation

- `LANGFUSE_FILTERING.md` - Detailed guide on filtering and usage
- `IMPLEMENTATION_SUMMARY.md` - This file

## Status

✅ **Complete and Ready to Use**

The implementation is complete, tested, and ready for production use. All AI Assistant traces now have proper tags and descriptive names for easy filtering in Langfuse.
