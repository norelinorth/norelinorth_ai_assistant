"""
Langfuse observability utilities for AI Provider
Provides centralized LLM tracing and monitoring for all apps
"""
from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password

# Graceful degradation: langfuse is optional
try:
	from langfuse import Langfuse
	LANGFUSE_AVAILABLE = True
except ImportError:
	LANGFUSE_AVAILABLE = False
	# Don't log error at import time - Langfuse is optional
	# Only notify user if they try to use it when it's not installed


_langfuse_client = None


def get_langfuse_client():
	"""
	Get or initialize Langfuse client if observability is enabled

	Returns:
		Langfuse client instance or None if not configured/enabled
	"""
	global _langfuse_client

	# Check if langfuse package is available
	if not LANGFUSE_AVAILABLE:
		return None

	try:
		# Get AI Provider configuration
		prov = frappe.get_single("AI Provider")

		# Check if Langfuse is enabled
		if not prov.enable_langfuse:
			return None

		# Return cached client if available
		if _langfuse_client is not None:
			return _langfuse_client

		# Get credentials
		public_key = prov.langfuse_public_key
		if not public_key:
			frappe.log_error(
				_("Langfuse public key not configured"),
				_("Langfuse Configuration Error")
			)
			return None

		secret_key = get_decrypted_password(
			"AI Provider", "AI Provider", "langfuse_secret_key", raise_exception=False
		)
		if not secret_key:
			frappe.log_error(
				_("Langfuse secret key not configured"),
				_("Langfuse Configuration Error")
			)
			return None

		# Use host from config (defaults to https://cloud.langfuse.com in DocType)
		host = prov.langfuse_host
		if not host:
			frappe.log_error(
				_("Langfuse host not configured"),
				_("Langfuse Configuration Error")
			)
			return None

		# Initialize Langfuse client
		_langfuse_client = Langfuse(
			public_key=public_key,
			secret_key=secret_key,
			host=host
		)

		return _langfuse_client

	except Exception as e:
		frappe.log_error(
			f"Failed to initialize Langfuse client: {str(e)}",
			_("Langfuse Initialization Error")
		)
		return None


def reset_langfuse_client():
	"""Reset the cached Langfuse client (useful after config changes)"""
	global _langfuse_client
	_langfuse_client = None


def flush_langfuse():
	"""Flush pending Langfuse events (useful before process exit)"""
	client = get_langfuse_client()
	if client:
		try:
			client.flush()
		except Exception as e:
			frappe.log_error(
				f"Failed to flush Langfuse events: {str(e)}",
				_("Langfuse Flush Error")
			)


@frappe.whitelist()
def validate_langfuse_config() -> dict[str, Any]:
	"""
	Validate Langfuse configuration

	Returns:
		Dictionary with validation status
	"""
	if not frappe.has_permission("AI Provider", "read"):
		frappe.throw(_("Not permitted to read AI Provider configuration"))

	try:
		prov = frappe.get_single("AI Provider")

		if not prov.enable_langfuse:
			return {
				"enabled": False,
				"configured": False,
				"status": "disabled",
				"message": _("Langfuse observability is not enabled")
			}

		# Check credentials
		has_public_key = bool(prov.langfuse_public_key)
		secret_key = get_decrypted_password(
			"AI Provider", "AI Provider", "langfuse_secret_key", raise_exception=False
		)
		has_secret_key = bool(secret_key)

		if not has_public_key or not has_secret_key:
			return {
				"enabled": True,
				"configured": False,
				"status": "incomplete",
				"message": _("Langfuse credentials incomplete")
			}

		# Try to initialize client
		client = get_langfuse_client()
		if client:
			return {
				"enabled": True,
				"configured": True,
				"status": "active",
				"message": _("Langfuse observability is active"),
				"host": prov.langfuse_host
			}
		else:
			return {
				"enabled": True,
				"configured": True,
				"status": "error",
				"message": _("Failed to initialize Langfuse client")
			}

	except Exception as e:
		frappe.log_error(
			f"Failed to validate Langfuse config: {str(e)}",
			_("Langfuse Validation Error")
		)
		return {
			"enabled": False,
			"configured": False,
			"status": "error",
			"message": str(e)
		}
