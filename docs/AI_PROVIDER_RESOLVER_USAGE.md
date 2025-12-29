# AI Provider Resolver - Site-Wide Usage Guide

## Overview
The AI Provider Resolver is a centralized service that allows any app in your Frappe/ERPNext installation to access AI capabilities using the configured AI Provider settings.

## Key Features
- **Centralized Configuration**: Single source of truth for AI settings
- **Site-Wide Access**: Any app can use the AI services
- **Security**: Permission-based access control
- **Provider Agnostic**: Supports multiple AI providers (currently OpenAI)
- **Error Handling**: Graceful fallbacks and error logging

## Available Methods

### 1. Get AI Configuration
```python
# Python (server-side)
from ai_assistant.ai_provider_resolver import get_ai_config
config = get_ai_config()

# Or via frappe.call
config = frappe.call('ai_assistant.ai_provider_resolver.get_ai_config')
```

**Returns:**
```python
{
    "provider": "OpenAI",
    "default_model": "gpt-3.5-turbo",
    "api_base_url": "https://api.openai.com/v1",
    "is_active": True,
    "api_key_status": "SET",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 45
}
```

### 2. Call AI API
```python
# Simple call
from ai_assistant.ai_provider_resolver import call_ai
response = call_ai("What is the capital of France?")

# With context
context = {"document": "Sales Order", "customer": "ABC Corp"}
response = call_ai(
    prompt="Summarize this order",
    context=json.dumps(context)
)

# With custom model
response = call_ai(
    prompt="Complex analysis task",
    model="gpt-4"
)
```

### 3. Validate AI Setup
```python
from ai_assistant.ai_provider_resolver import validate_ai_setup
validation = validate_ai_setup()

# Returns validation status
{
    "provider_configured": True,
    "api_key_configured": True,
    "model_configured": True,
    "connection_test": True,
    "status": "valid",
    "errors": []
}
```

## Usage Examples

### Example 1: In a Custom App's DocType
```python
# In your_app/your_module/doctype/your_doctype/your_doctype.py

import frappe
from ai_assistant.ai_provider_resolver import AIProviderResolver

class YourDocType(Document):
    def validate(self):
        # Use AI to validate or enhance data
        resolver = AIProviderResolver()
        
        # Get AI suggestion for description
        if not self.description and self.title:
            try:
                prompt = f"Generate a brief description for: {self.title}"
                self.description = resolver.call_ai_api(prompt)
            except Exception as e:
                frappe.log_error(f"AI generation failed: {e}")
```

### Example 2: In a Server Script
```python
# Server Script (Python)
import json

# Get configuration
config = frappe.call('ai_assistant.ai_provider_resolver.get_ai_config')

if config.get('api_key_status') == 'SET':
    # Make AI call
    context = {
        "doctype": doc.doctype,
        "name": doc.name,
        "data": doc.as_dict()
    }
    
    response = frappe.call(
        'ai_assistant.ai_provider_resolver.call_ai',
        prompt="Analyze this document",
        context=json.dumps(context)
    )
    
    # Use response
    frappe.msgprint(response)
```

### Example 3: In Client-Side JavaScript
```javascript
// In a Form Script or Custom App JS

frappe.call({
    method: 'ai_assistant.ai_provider_resolver.get_ai_config',
    callback: function(r) {
        if (r.message && r.message.api_key_status === 'SET') {
            // AI is configured, enable AI features
            frm.add_custom_button('AI Assist', function() {
                callAI(frm);
            });
        }
    }
});

function callAI(frm) {
    const context = {
        doctype: frm.doctype,
        name: frm.docname,
        fields: frm.doc
    };
    
    frappe.call({
        method: 'ai_assistant.ai_provider_resolver.call_ai',
        args: {
            prompt: 'Suggest improvements for this document',
            context: JSON.stringify(context)
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint({
                    title: 'AI Suggestions',
                    message: r.message,
                    indicator: 'blue'
                });
            }
        }
    });
}
```

### Example 4: In a Report
```python
# In your_app/your_module/report/your_report/your_report.py

def execute(filters=None):
    from ai_assistant.ai_provider_resolver import AIProviderResolver
    
    # Get report data
    data = get_report_data(filters)
    
    # Add AI insights if available
    try:
        resolver = AIProviderResolver()
        insights = resolver.call_ai_api(
            prompt=f"Analyze these metrics: {summarize_data(data)}",
            system_message="Provide brief business insights"
        )
        
        # Add insights to report
        columns, data = add_insights_column(columns, data, insights)
    except:
        pass  # AI not available, continue without insights
    
    return columns, data
```

## Permissions

The AI Provider Resolver respects Frappe's permission system:

- **Read AI Provider**: Required to view configuration
- **Write AI Provider**: Required to access credentials and make AI calls
- **AI Assistant Session Write**: Required to use the AI services

## Error Handling

The resolver provides comprehensive error handling:

```python
try:
    response = call_ai("Your prompt")
except Exception as e:
    # Errors are automatically logged
    # Handle gracefully
    fallback_response = generate_local_response()
```

## Testing

Run the test script to verify your installation:

```bash
cd frappe-bench
bench --site localhost execute ai_assistant.test_ai_resolver.test_resolver
```

## Security Considerations

1. **API Keys**: Stored encrypted using Frappe's password field
2. **Permissions**: Role-based access control
3. **Validation**: Input validation and sanitization
4. **Logging**: All errors logged for audit

## Extending the Resolver

To add support for new AI providers:

1. Extend the `AIProviderResolver` class
2. Add provider-specific methods
3. Update the `call_ai_api` method to route to your provider
4. Add configuration fields to AI Provider DocType

## Troubleshooting

### AI calls failing
1. Check configuration: `validate_ai_setup()`
2. Verify permissions for the user
3. Check error logs: `bench --site localhost console` then `frappe.get_all("Error Log", limit=5)`

### Permission denied
Ensure user has the "AI Assistant User" role or appropriate permissions on AI Provider DocType.

### Configuration not found
Ensure AI Provider Single DocType exists and is configured:
```python
frappe.get_single("AI Provider")
```

## Support

For issues or questions:
1. Check the error logs in ERPNext
2. Run the test script for diagnostics
3. Verify AI Provider configuration in the UI