"""
Simplified AI Provider API for multi-app usage
No unnecessary class wrappers - just clean functions
With integrated Langfuse observability
"""
from __future__ import annotations

import json
from typing import Any

import frappe
import requests
from frappe import _
from frappe.utils.password import get_decrypted_password

from ai_assistant.ai_observability import get_langfuse_client


@frappe.whitelist()
def get_ai_config() -> dict[str, Any]:
    """Get AI Provider configuration (safe for all apps)"""
    if not frappe.has_permission("AI Provider", "read"):
        frappe.throw(_("Not permitted to read AI Provider configuration"))

    try:
        prov = frappe.get_single("AI Provider")

        # Check if API key is set without exposing it
        api_key_status = "NOT_SET"
        try:
            api_key = get_decrypted_password(
                "AI Provider", "AI Provider", "api_key", raise_exception=False
            )
            if api_key and api_key.strip():
                api_key_status = "SET"
        except Exception:
            pass

        return {
            "provider": prov.provider or "",
            "default_model": prov.default_model or "",
            "api_base_url": prov.api_base_url or "",
            "is_active": bool(prov.is_active),
            "api_key_status": api_key_status
        }
    except frappe.DoesNotExistError:
        frappe.throw(_("AI Provider not configured"))


@frappe.whitelist()
def call_ai(prompt: str, context: str | None = None, model: str | None = None, source: str | None = None) -> str:
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
    if not frappe.has_permission("AI Provider", "read"):
        frappe.throw(_("Not permitted to use AI services"))

    # Get provider configuration
    prov = frappe.get_single("AI Provider")

    if not prov.is_active:
        frappe.throw(_("AI Provider is not active"))

    # Get API key
    api_key = get_decrypted_password(
        "AI Provider", "AI Provider", "api_key", raise_exception=False
    )
    if not api_key:
        frappe.throw(_("API Key not configured"))

    # Prepare context if provided
    context_data = None
    if context:
        try:
            context_data = json.loads(context) if isinstance(context, str) else context
        except json.JSONDecodeError:
            context_data = {"text": context}

    # Build messages
    messages = [{
        "role": "system",
        "content": _("You are a helpful assistant. Provide clear, concise answers.")
    }]

    if context_data:
        messages.append({
            "role": "system",
            "content": f"Context: {json.dumps(context_data, default=str)}"
        })

    messages.append({"role": "user", "content": prompt})

    # Validate required configuration (no hardcoded fallbacks)
    if not prov.api_base_url:
        frappe.throw(_("Please configure API Base URL in AI Provider settings"))

    if not prov.default_model and not model:
        frappe.throw(_("Please configure Default Model in AI Provider settings or provide a model parameter"))

    # Use provided model or default model from config
    model = model or prov.default_model
    base_url = prov.api_base_url

    # Get Langfuse client if enabled
    langfuse_client = get_langfuse_client()
    use_tracing = bool(langfuse_client)

    # Temperature and max_tokens (sensible defaults)
    temperature = 0.7
    max_tokens = 2000

    # Helper function for the actual API call (eliminates duplication)
    def make_api_call():
        """Make the actual OpenAI API call"""
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=45
        )
        response.raise_for_status()
        return response.json()

    # Make API call with optional tracing
    try:
        if use_tracing:
            # Parse context to extract doctype information for better trace organization
            trace_metadata = {
                "provider": prov.provider,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "has_context": bool(context_data),
                "user": frappe.session.user,
                "source": source or "unknown"  # Track which app/system is making the call
            }

            # Add document context to metadata if available
            if context_data:
                try:
                    # context_data is already a dict (parsed in lines 78-83)
                    if isinstance(context_data, dict) and "scalar" in context_data:
                        scalar = context_data.get("scalar", {})
                        if "_doctype" in scalar:
                            trace_metadata["doctype"] = scalar["_doctype"]
                        if "_name" in scalar:
                            trace_metadata["document_name"] = scalar["_name"]
                    # Also check if context_data has "text" key (plain text context)
                    elif isinstance(context_data, dict) and "text" in context_data:
                        # Plain text context - no doctype to extract
                        pass
                except Exception as e:
                    # If parsing fails, just continue without doctype metadata
                    # Log for debugging but don't fail tracing
                    frappe.logger().debug(f"Could not parse context for Langfuse metadata: {str(e)}")
                    pass

            # Build tags for metadata (Langfuse 3.8.1 doesn't support tags parameter on start_as_current_generation)
            tags = []
            if source:
                tags.append(source)  # e.g., "ai_assistant", "journal_validation"
            if context_data and isinstance(context_data, dict) and "scalar" in context_data:
                if "_doctype" in context_data["scalar"]:
                    tags.append(context_data["scalar"]["_doctype"])  # e.g., "Sales Order"

            # Add tags to metadata for filtering
            if tags:
                trace_metadata["tags"] = tags

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
                metadata=trace_metadata
            ) as generation:
                # Make API call
                data = make_api_call()

                # Extract response
                if "choices" in data and len(data["choices"]) > 0:
                    ai_response = data["choices"][0]["message"]["content"]

                    # Update trace with results
                    usage = data.get("usage", {})
                    generation.update(
                        output=ai_response,
                        usage={
                            "input": usage.get("prompt_tokens"),
                            "output": usage.get("completion_tokens"),
                            "total": usage.get("total_tokens")
                        }
                    )
                    # Don't flush here - let Langfuse SDK handle it automatically
                    # Flushing inside context manager causes duplicates
                    return ai_response
                else:
                    frappe.throw(_("Invalid response from AI API"))
        else:
            # No tracing - just make the call
            data = make_api_call()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                frappe.throw(_("Invalid response from AI API"))

    except requests.exceptions.Timeout:
        frappe.throw(_("AI API request timed out"))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            frappe.throw(_("Invalid API key"))
        elif e.response.status_code == 429:
            frappe.throw(_("API rate limit exceeded"))
        else:
            frappe.throw(_("AI API error: {0}").format(str(e)))
    except Exception as e:
        # If tracing fails, try without tracing
        if use_tracing:
            frappe.log_error(
                f"Langfuse tracing failed: {str(e)}\n{frappe.get_traceback()}",
                _("Langfuse Tracing Error")
            )
            # Retry without tracing
            try:
                data = make_api_call()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    frappe.throw(_("Invalid response from AI API"))
            except Exception:
                # If retry also fails, re-raise
                raise
        else:
            frappe.log_error(f"AI API Error: {str(e)}", "AI Provider")
            frappe.throw(_("Failed to call AI API"))


@frappe.whitelist()
def validate_ai_config() -> dict[str, bool]:
    """Validate AI configuration (for any app to check)"""
    if not frappe.has_permission("AI Provider", "read"):
        frappe.throw(_("Not permitted"))

    try:
        config = get_ai_config()
        return {
            "configured": config.get("api_key_status") == "SET" and config.get("provider"),
            "active": config.get("is_active", False)
        }
    except Exception:
        return {"configured": False, "active": False}
