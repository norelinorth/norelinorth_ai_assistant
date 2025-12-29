from __future__ import annotations

import frappe
from frappe import _


def inject_ai_assistant(doc, method):
    """Inject AI Assistant configuration into doctype on load"""
    if not frappe.has_permission("AI Assistant Session", "read"):
        return

    # Check if user has required role
    user_roles = frappe.get_roles(frappe.session.user)
    if "AI Assistant User" not in user_roles:
        return

    # Check if AI Provider is configured
    try:
        provider = frappe.get_single("AI Provider")
        if not provider.is_active:
            return

        # Add AI assistant flag to document
        doc.set_onload("ai_assistant_enabled", True)
        doc.set_onload("ai_assistant_config", {
            "provider": provider.provider,
            "model": provider.default_model
        })
    except frappe.DoesNotExistError:
        frappe.log_error("AI Provider not configured", "AI Assistant")
    except Exception as e:
        frappe.log_error(f"Error loading AI Assistant: {str(e)}", "AI Assistant")

def validate_ai_permission(doc, method):
    """Validate AI Assistant permissions before save"""
    # This is called during validate, we just ensure proper logging
    if hasattr(doc, "_ai_assistant_used") and doc._ai_assistant_used:
        if not frappe.has_permission("AI Assistant Session", "write"):
            frappe.throw(_("You don't have permission to use AI Assistant"))
