from __future__ import annotations

app_name = "norelinorth_ai_assistant"
app_title = "Noreli North AI Assistant"
app_publisher = "Noreli North"
app_description = "Embedded AI Assistant inside ERPNext DocTypes with Langfuse observability."
app_icon = "octicon octicon-hubot"
app_color = "#4F46E5"
app_license = "MIT"
app_version = "2.2.13"
app_home = "https://github.com/norelinorth/norelinorth_ai_assistant"

required_apps = ["frappe"]

after_install = "norelinorth_ai_assistant.install.after_install"

user_data_fields = [
    {"doctype": "AI Assistant Session", "filter_by": "owner", "redact_fields": [], "partial": 1},
    {"doctype": "AI Message", "filter_by": "owner", "redact_fields": ["content"], "partial": 1},
]

# DocType event hooks for AI Assistant integration
doc_events = {
    "Sales Order": {
        "onload": "norelinorth_ai_assistant.doctype_hooks.inject_ai_assistant",
        "validate": "norelinorth_ai_assistant.doctype_hooks.validate_ai_permission"
    },
    "Purchase Order": {
        "onload": "norelinorth_ai_assistant.doctype_hooks.inject_ai_assistant",
        "validate": "norelinorth_ai_assistant.doctype_hooks.validate_ai_permission"
    },
    "Sales Invoice": {
        "onload": "norelinorth_ai_assistant.doctype_hooks.inject_ai_assistant",
        "validate": "norelinorth_ai_assistant.doctype_hooks.validate_ai_permission"
    },
    "Purchase Invoice": {
        "onload": "norelinorth_ai_assistant.doctype_hooks.inject_ai_assistant",
        "validate": "norelinorth_ai_assistant.doctype_hooks.validate_ai_permission"
    },
    "Journal Entry": {
        "onload": "norelinorth_ai_assistant.doctype_hooks.inject_ai_assistant",
        "validate": "norelinorth_ai_assistant.doctype_hooks.validate_ai_permission"
    }
}

# Include JS file for client-side integration
app_include_js = "/assets/norelinorth_ai_assistant/js/ai_assistant_integration.js"

# Also include in doctype-specific JS
doctype_js = {
    "Sales Order": "public/js/ai_assistant_integration.js",
    "Purchase Order": "public/js/ai_assistant_integration.js",
    "Sales Invoice": "public/js/ai_assistant_integration.js",
    "Purchase Invoice": "public/js/ai_assistant_integration.js",
    "Journal Entry": "public/js/ai_assistant_integration.js"
}

# Whitelisted methods for other apps to use AI Provider
# These are simple, direct functions without unnecessary class wrappers
override_whitelisted_methods = {
    # Core AI Provider API - available to all apps
    "norelinorth_ai_assistant.ai_provider_api.get_ai_config": "norelinorth_ai_assistant.ai_provider_api.get_ai_config",
    "norelinorth_ai_assistant.ai_provider_api.call_ai": "norelinorth_ai_assistant.ai_provider_api.call_ai",
    "norelinorth_ai_assistant.ai_provider_api.validate_ai_config": "norelinorth_ai_assistant.ai_provider_api.validate_ai_config",
}

# Standard DocType permissions
standard_doctype_permissions = {
    "AI Provider": ["System Manager", "AI Assistant Admin"],
    "AI Assistant Session": ["AI Assistant User", "AI Assistant Admin"],
    "AI Message": ["AI Assistant User", "AI Assistant Admin"]
}
