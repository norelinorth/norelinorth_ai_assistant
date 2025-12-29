from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from ai_assistant.ai_provider_api import call_ai, get_ai_config


@frappe.whitelist()
def start_session(target_doctype: str | None = None, target_name: str | None = None):
    """Start a new AI Assistant session"""
    # Check base permission
    if not frappe.has_permission("AI Assistant Session", "create"):
        frappe.throw(_("Not permitted to create AI Assistant sessions"))

    # Validate context if provided
    if target_doctype and target_name:
        # Ensure user has read access to the target doc
        if not frappe.has_permission(target_doctype, "read", target_name):
            frappe.throw(_("Not permitted to read the target document"))

    doc = frappe.get_doc({
        "doctype": "AI Assistant Session",
        "status": "Active",
        "target_doctype": target_doctype,
        "target_name": target_name,
        "started_on": now_datetime(),
    }).insert()

    frappe.db.commit()
    return {"name": doc.name}


@frappe.whitelist()
def chat_once(session: str, prompt: str) -> dict:
    """Send a message to AI and get response"""
    # Permission check
    if not frappe.has_permission("AI Assistant Session", "write"):
        frappe.throw(_("Not permitted to use AI Assistant"))

    prompt = (prompt or "").strip()
    if not prompt:
        frappe.throw(_("Prompt is required"))

    # Get session
    try:
        sess = frappe.get_doc("AI Assistant Session", session)
    except frappe.DoesNotExistError:
        frappe.throw(_("Session not found"))

    # Check ownership
    if sess.owner != frappe.session.user and not frappe.has_permission("AI Assistant Session", "write", sess):
        frappe.throw(_("Not permitted to access this session"))

    # Extract context if available
    context: dict[str, Any] | None = None
    if sess.target_doctype and sess.target_name:
        # Check user can read the target doc
        if not frappe.has_permission(sess.target_doctype, "read", sess.target_name):
            frappe.throw(_("Not permitted to read the target document"))
        context = _extract_context(sess.target_doctype, sess.target_name)

    # Persist user message
    sess.append("messages", {"role": "user", "content": prompt})
    sess.save(ignore_permissions=True)
    frappe.db.commit()

    # Prepare context for AI
    system_context = None
    if context:
        system_context = json.dumps(context, default=str)

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

    except Exception as e:
        frappe.log_error(f"AI API Error: {str(e)}\n{frappe.get_traceback()}", "AI Assistant")
        frappe.throw(_("AI service temporarily unavailable. Please try again later."))

    # Persist assistant message
    sess.reload()
    sess.append("messages", {"role": "assistant", "content": reply})
    sess.last_activity = now_datetime()
    sess.save(ignore_permissions=True)
    frappe.db.commit()

    return {"reply": reply}


def _extract_context(doctype: str, name: str) -> dict:
    """Build a structured context dict from the database using DocType metadata"""
    meta = frappe.get_meta(doctype)
    doc = frappe.get_doc(doctype, name)

    # Extract scalar fields
    scalar = {}
    for df in meta.get("fields"):
        if df.hidden:
            continue

        ft = (df.fieldtype or "").strip()
        # Skip large text and binary fields
        if ft in {"Long Text", "Text", "Text Editor", "HTML", "Image", "Attach", "Attach Image", "Code"}:
            continue

        val = doc.get(df.fieldname)
        if val is None:
            continue

        # Include commonly useful field types
        if ft in {"Data", "Int", "Float", "Currency", "Percent", "Select", "Date", "Datetime", "Time", "Check", "Link", "Dynamic Link"}:
            scalar[df.fieldname] = val

    # Add basic identity fields
    scalar.update({
        "_doctype": doctype,
        "_name": name,
        "_owner": getattr(doc, "owner", None),
        "_modified": getattr(doc, "modified", None),
        "_title": getattr(doc, meta.title_field or "", None)
    })

    # Extract child table data
    children = {}
    for df in meta.get("fields"):
        if (df.fieldtype or "").strip() != "Table":
            continue

        table_doctype = df.options
        if not table_doctype:
            continue

        rows = doc.get(df.fieldname) or []
        if not rows:
            continue

        # Get child table metadata
        row_meta = frappe.get_meta(table_doctype)
        row_fields = [
            f for f in row_meta.get("fields")
            if f.fieldtype in {"Data", "Int", "Float", "Currency", "Percent", "Select", "Date", "Datetime", "Time", "Check", "Link", "Dynamic Link"}
            and not f.hidden
        ]

        # Extract row data
        row_dicts = []
        for row in rows[:10]:  # Limit to first 10 rows
            item = {}
            for f in row_fields:
                v = row.get(f.fieldname)
                if v is not None:
                    item[f.fieldname] = v
            if item:
                row_dicts.append(item)

        if row_dicts:
            children[df.fieldname] = row_dicts

    return {"scalar": scalar, "children": children}


@frappe.whitelist()
def get_provider_config():
    """Get AI Provider configuration status"""
    return get_ai_config()


@frappe.whitelist()
def test_context_extraction(doctype: str, name: str):
    """Test dynamic context extraction - for debugging"""
    if not frappe.has_permission(doctype, "read", name):
        frappe.throw(_("Not permitted to read this document"))

    # Extract context using real database data
    context = _extract_context(doctype, name)

    # Add debug metadata
    meta = frappe.get_meta(doctype)
    context["_debug_info"] = {
        "total_fields": len(meta.get("fields")),
        "scalar_fields_extracted": len(context.get("scalar", {})),
        "child_tables_found": len(context.get("children", {})),
        "doctype_module": meta.module,
        "extraction_method": "dynamic_frappe_meta"
    }

    return context
