from __future__ import annotations

import json
from typing import Any

import frappe
import requests
from frappe import _
from frappe.utils.password import get_decrypted_password


class AIProviderResolver:
	"""
	Centralized AI Provider configuration resolver for site-wide access.
	This class provides a unified interface for all apps to access AI configuration.
	"""

	@staticmethod
	@frappe.whitelist(allow_guest=False)
	def get_ai_provider_config() -> dict[str, Any]:
		"""
		Get the current AI provider configuration.
		Returns configuration details without sensitive data.
		"""
		if not frappe.has_permission("AI Provider", "read"):
			frappe.throw(_("Insufficient permissions to access AI Provider"), frappe.PermissionError)

		try:
			prov = frappe.get_single("AI Provider")

			# Check API key status
			api_key_status = AIProviderResolver._check_api_key_status()

			return {
				"provider": prov.provider or "",
				"default_model": prov.default_model or "",
				"api_base_url": prov.api_base_url or "",
				"is_active": bool(prov.is_active),
				"api_key_status": api_key_status,
				"temperature": prov.temperature if hasattr(prov, 'temperature') else 0.7,
				"max_tokens": prov.max_tokens if hasattr(prov, 'max_tokens') else 2000,
				"timeout": prov.timeout if hasattr(prov, 'timeout') else 45
			}
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "AI Provider Config Error")
			return {"error": str(e), "status": "error"}

	@staticmethod
	def _check_api_key_status() -> str:
		"""Check if API key is configured."""
		try:
			api_key = get_decrypted_password(
				"AI Provider", "AI Provider", "api_key", raise_exception=False
			)
			if api_key and api_key.strip():
				return "SET"
		except Exception:
			return "ERROR"
		return "NOT_SET"

	@staticmethod
	@frappe.whitelist(allow_guest=False)
	def get_api_credentials() -> tuple[str, str, str]:
		"""
		Get API credentials for AI provider.
		Returns: (api_key, base_url, provider)
		Only accessible to users with write permission on AI Provider.
		"""
		if not frappe.has_permission("AI Provider", "write"):
			frappe.throw(_("Insufficient permissions to access AI Provider credentials"), frappe.PermissionError)

		prov = frappe.get_single("AI Provider")

		if not prov.is_active:
			frappe.throw(_("AI Provider is not active. Please enable it in AI Provider settings."))

		provider = (prov.provider or "").strip()
		if not provider:
			frappe.throw(_("AI Provider is not configured. Please set Provider in AI Provider settings."))

		api_key = get_decrypted_password(
			"AI Provider", "AI Provider", "api_key", raise_exception=False
		)
		if not api_key:
			frappe.throw(_("API Key is not configured in AI Provider settings."))

		# Get base URL from configuration, require it to be set
		base_url = (prov.api_base_url or "").strip()
		if not base_url:
			# Default based on provider type
			if provider == "OpenAI":
				base_url = "https://api.openai.com/v1"
			else:
				frappe.throw(_("API Base URL is required for non-OpenAI providers."))

		return api_key, base_url, provider

	@staticmethod
	@frappe.whitelist(allow_guest=False)
	def call_ai_api(prompt: str, context: dict[str, Any] | None = None,
					model: str | None = None, system_message: str | None = None) -> str:
		"""
		Make a call to the configured AI API.

		Args:
			prompt: User prompt/question
			context: Optional context dictionary
			model: Optional model override (uses default if not specified)
			system_message: Optional system message override

		Returns:
			AI response as string
		"""
		if not frappe.has_permission("AI Assistant Session", "write"):
			frappe.throw(_("Insufficient permissions to use AI Assistant"), frappe.PermissionError)

		# Get credentials
		api_key, base_url, provider = AIProviderResolver.get_api_credentials()

		# Get configuration
		config = AIProviderResolver.get_ai_provider_config()
		model = model or config.get("default_model")

		if not model:
			frappe.throw(_("No AI model configured. Please set Default Model in AI Provider settings."))

		# Default system message if not provided
		if not system_message:
			system_message = _("You are a helpful ERPNext/Frappe assistant. Provide clear, concise answers based on the context provided.")

		# Build messages
		messages = [{"role": "system", "content": system_message}]

		if context:
			context_json = json.dumps(context, default=str)
			messages.append({"role": "system", "content": f"Context:\n{context_json}"})

		messages.append({"role": "user", "content": prompt})

		# Make API call based on provider
		if provider.lower() == "openai":
			return AIProviderResolver._call_openai(
				api_key, base_url, model, messages,
				config.get("temperature", 0.7),
				config.get("max_tokens", 2000),
				config.get("timeout", 45)
			)
		else:
			frappe.throw(_("Provider {0} is not yet supported.").format(provider))

	@staticmethod
	def _call_openai(api_key: str, base_url: str, model: str, messages: list,
					temperature: float = 0.7, max_tokens: int = 2000, timeout: int = 45) -> str:
		"""Call OpenAI-compatible API."""
		payload = {
			"model": model,
			"messages": messages,
			"temperature": temperature,
			"max_tokens": max_tokens
		}

		headers = {
			"Authorization": f"Bearer {api_key}",
			"Content-Type": "application/json"
		}

		try:
			response = requests.post(
				f"{base_url.rstrip('/')}/chat/completions",
				headers=headers,
				json=payload,
				timeout=timeout
			)
			response.raise_for_status()
			data = response.json()
			return data["choices"][0]["message"]["content"]
		except requests.exceptions.Timeout:
			frappe.throw(_("AI API request timed out. Please try again."))
		except requests.exceptions.RequestException as e:
			frappe.log_error(frappe.get_traceback(), "AI API Request Error")
			frappe.throw(_("Failed to call AI API: {0}").format(str(e)))

	@staticmethod
	@frappe.whitelist(allow_guest=False)
	def validate_configuration() -> dict[str, Any]:
		"""
		Validate the current AI provider configuration.
		Tests connectivity and returns validation results.
		"""
		if not frappe.has_permission("AI Provider", "write"):
			frappe.throw(_("Insufficient permissions to validate AI Provider configuration"), frappe.PermissionError)

		results = {
			"provider_configured": False,
			"api_key_configured": False,
			"model_configured": False,
			"connection_test": False,
			"errors": []
		}

		try:
			# Check basic configuration
			config = AIProviderResolver.get_ai_provider_config()

			if config.get("provider"):
				results["provider_configured"] = True
			else:
				results["errors"].append("Provider not configured")

			if config.get("api_key_status") == "SET":
				results["api_key_configured"] = True
			else:
				results["errors"].append("API key not configured")

			if config.get("default_model"):
				results["model_configured"] = True
			else:
				results["errors"].append("Default model not configured")

			# Test connection if all basic config is present
			if all([results["provider_configured"],
					results["api_key_configured"],
					results["model_configured"]]):
				try:
					response = AIProviderResolver.call_ai_api(
						"Test connection",
						system_message="Reply with 'Connection successful'"
					)
					if response:
						results["connection_test"] = True
				except Exception as e:
					results["errors"].append(f"Connection test failed: {str(e)}")

			results["status"] = "valid" if results["connection_test"] else "invalid"

		except Exception as e:
			results["errors"].append(str(e))
			results["status"] = "error"

		return results


# Utility functions for easy access from other apps
@frappe.whitelist(allow_guest=False)
def get_ai_config():
	"""Shorthand for getting AI configuration."""
	resolver = AIProviderResolver()
	return resolver.get_ai_provider_config()


@frappe.whitelist(allow_guest=False)
def call_ai(prompt: str, context: str | None = None, model: str | None = None):
	"""
	Simplified AI call interface for other apps.
	Context can be passed as JSON string.
	"""
	resolver = AIProviderResolver()

	# Parse context if provided as string
	context_dict = None
	if context:
		try:
			context_dict = json.loads(context)
		except json.JSONDecodeError:
			# If not JSON, treat as plain text context
			context_dict = {"text": context}

	return resolver.call_ai_api(prompt, context_dict, model)


@frappe.whitelist(allow_guest=False)
def validate_ai_setup():
	"""Validate AI setup for other apps."""
	resolver = AIProviderResolver()
	return resolver.validate_configuration()
