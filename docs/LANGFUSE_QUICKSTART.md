# Langfuse Observability - Quick Start Guide

## 30-Second Setup

### 1. Get Credentials (5 min)
1. Go to https://cloud.langfuse.com
2. Sign up / Log in
3. Create new project
4. Copy **Public Key** and **Secret Key**

### 2. Configure ERPNext (2 min)
1. Open **AI Provider** in ERPNext
2. Scroll to **Observability Settings**
3. ✓ Enable **Langfuse Observability**
4. Paste **Public Key**
5. Paste **Secret Key**
6. Save

### 3. Done! 🎉
All AI calls are now automatically traced to Langfuse.

## For Developers

### Zero Code Changes Required

**Before Langfuse:**
```python
from ai_assistant.ai_provider_api import call_ai

response = call_ai(
    prompt="Analyze this data",
    context=json.dumps(my_data)
)
```

**After Langfuse:**
```python
# EXACT SAME CODE - automatically traced! 🚀
from ai_assistant.ai_provider_api import call_ai

response = call_ai(
    prompt="Analyze this data",
    context=json.dumps(my_data)
)
```

That's it. No imports, no wrappers, no changes.

## What You Get

### In Langfuse Dashboard

**Every AI call shows:**
- ✓ User who made the call
- ✓ Full prompt and context
- ✓ AI response
- ✓ Token usage (prompt + completion)
- ✓ Cost estimate
- ✓ Latency
- ✓ Timestamp

### Analytics View

- 📊 Total tokens used
- 💰 Total cost
- 👥 Usage per user
- 📈 Calls over time
- 🎯 Model distribution

## Verify It's Working

### Quick Test

```python
# Run in bench console
from ai_assistant.ai_provider_api import call_ai

# Make a test call
response = call_ai(prompt="What is 2+2?")
print(response)

# Check Langfuse dashboard - you should see a new trace!
```

### Check Configuration

```python
# Run in bench console
from ai_assistant.ai_observability import validate_langfuse_config

status = validate_langfuse_config()
print(status)

# Should show: {'status': 'active', ...}
```

## Common Questions

### Q: Do I need to change my code?
**A:** No. Existing code works automatically.

### Q: What if I don't configure Langfuse?
**A:** AI calls work normally. Tracing is optional.

### Q: Does it slow down AI calls?
**A:** No. Tracing is async and non-blocking (~5ms overhead).

### Q: What if Langfuse is down?
**A:** AI calls continue normally. Errors logged, not thrown.

### Q: Can I use self-hosted Langfuse?
**A:** Yes. Set **Langfuse Host** to your instance URL.

### Q: How do I disable it?
**A:** Uncheck **Enable Langfuse Observability** in AI Provider.

## Example: Journal Validation

```python
# Your code (no Langfuse imports needed!)
from ai_assistant.ai_provider_api import call_ai

def validate_journal(doc):
    response = call_ai(
        prompt="Check if this journal entry is valid",
        context=json.dumps({
            "total_debit": doc.total_debit,
            "total_credit": doc.total_credit,
            "accounts": [a.as_dict() for a in doc.accounts]
        })
    )
    return response
```

**Result:** Every validation automatically traced with full context.

## Useful Links

- **Full Documentation**: [LANGFUSE_OBSERVABILITY.md](LANGFUSE_OBSERVABILITY.md)
- **Langfuse Dashboard**: https://cloud.langfuse.com
- **Langfuse Docs**: https://langfuse.com/docs

## Pro Tips

### 1. Add Descriptive Context
```python
# Good - helps debugging in Langfuse
context = {
    "doctype": "Journal Entry",
    "name": doc.name,
    "purpose": "validation"
}

# Okay - but less useful
context = doc.as_dict()
```

### 2. Monitor Token Usage
Check Langfuse analytics weekly to:
- Identify high-cost features
- Optimize prompts
- Plan budgets

### 3. Use Filters
In Langfuse dashboard:
- Filter by user to see individual usage
- Filter by date for cost trends
- Search traces to debug issues

## Troubleshooting

### Not seeing traces?

1. **Check configuration:**
   ```python
   from ai_assistant.ai_observability import validate_langfuse_config
   print(validate_langfuse_config())
   ```

2. **Check Error Log:**
   Go to `Desk → Tools → Error Log`
   Look for "Langfuse" errors

3. **Verify credentials:**
   - Public Key and Secret Key correct?
   - Copied without extra spaces?

4. **Check enable checkbox:**
   Is **Enable Langfuse Observability** checked?

### AI calls failing?

Langfuse issues should NOT affect AI calls. If AI calls fail:
1. Check Error Log for actual error
2. Test with Langfuse disabled to isolate
3. Verify OpenAI API key is valid

## Support

**Quick Help:**
- Error Log: `Desk → Tools → Error Log`
- Test: `validate_langfuse_config()`
- Docs: `LANGFUSE_OBSERVABILITY.md`

**Need More Help?**
- Langfuse Docs: https://langfuse.com/docs
- Langfuse Discord: https://discord.gg/7NXusRtqYU

---

**That's it!** You're now tracking all AI calls with zero code changes. 🚀
