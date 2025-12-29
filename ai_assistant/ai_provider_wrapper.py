"""
AI Provider Wrapper for Variance Analysis Integration

This module bridges the ai_assistant's AI Provider DocType with the
variance_analysis app's expected callable interface.

Installation:
1. This file is automatically installed with the ai_assistant app
2. Configure in site_config.json:
   "ai_provider_callable": "ai_assistant.ai_provider_wrapper.generate_text"
3. Set API key using: bench --site {site} set-password "AI Provider" "AI Provider" --fieldname api_key
"""


import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password

from ai_assistant.ai_provider_resolver import AIProviderResolver


def generate_text(prompt: str, **kwargs) -> str:
	"""
	Generate text using AI Provider configuration.

	This function is called by variance_analysis app via site_config.json
	setting: "ai_provider_callable": "ai_assistant.ai_provider_wrapper.generate_text"

	Args:
		prompt: The text prompt to send to the AI
		**kwargs: Additional arguments (ignored for compatibility)

	Returns:
		Generated text response from the AI provider
	"""
	try:
		# Check if AI Provider is configured
		if not frappe.db.exists("AI Provider", "AI Provider"):
			return "AI Provider is not configured. Please configure AI Provider in Settings."

		provider_doc = frappe.get_doc("AI Provider", "AI Provider")

		# Check if active
		if not provider_doc.is_active:
			return "AI Provider is not active. Please enable it in AI Provider settings."

		# Check for API key
		api_key = get_decrypted_password(
			"AI Provider", "AI Provider", "api_key", raise_exception=False
		)

		if not api_key:
			return "API Key is not configured in AI Provider settings."

		# Use the AIProviderResolver to make the actual API call
		resolver = AIProviderResolver()

		# Call the AI API with the prompt
		response = resolver.call_ai_api(
			prompt=prompt,
			context=kwargs.get('context'),
			model=provider_doc.default_model,
			system_message=kwargs.get('system_message')
		)

		return response

	except frappe.PermissionError:
		return "Insufficient permissions to access AI Provider."
	except Exception as e:
		frappe.log_error(f"AI Provider Wrapper Error: {str(e)}\n{frappe.get_traceback()}", "AI Provider Wrapper")
		return _("AI analysis failed. Please check Error Log for details.")

# Alternative function name for compatibility
def call_ai(prompt: str, **kwargs) -> str:
	"""Alias for generate_text for compatibility."""
	return generate_text(prompt, **kwargs)
