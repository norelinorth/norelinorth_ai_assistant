"""
Test AI Provider Wrapper

Tests wrapper module for variance analysis integration
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ai_assistant.ai_provider_wrapper import call_ai, generate_text


class TestAIProviderWrapper(unittest.TestCase):
	"""
	Test AI Provider Wrapper functions

	Test Coverage:
	- generate_text() - main function for variance analysis
	- call_ai() - alias function
	- Error handling and graceful degradation
	- Permission handling
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

	def setUp(self):
		"""Set up before each test"""
		frappe.db.rollback()
		frappe.set_user("Administrator")

		# Configure AI Provider
		self.provider = frappe.get_single("AI Provider")
		self.provider.provider = "OpenAI"
		self.provider.api_key = "test_api_key_wrapper"
		self.provider.api_base_url = "https://api.openai.com/v1"
		self.provider.default_model = "gpt-4o-mini"
		self.provider.is_active = 1
		self.provider.save()
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	@patch('ai_assistant.ai_provider_wrapper.AIProviderResolver')
	def test_01_generate_text_success(self, mock_resolver_class):
		"""Test successful text generation"""
		mock_resolver = MagicMock()
		mock_resolver.call_ai_api.return_value = "Generated response"
		mock_resolver_class.return_value = mock_resolver

		result = generate_text("Test prompt")

		self.assertEqual(result, "Generated response")

	def test_02_generate_text_inactive_provider(self):
		"""Test generate_text when provider inactive"""
		self.provider.is_active = 0
		self.provider.save()
		frappe.db.commit()

		result = generate_text("Test prompt")

		self.assertIn("not active", result.lower())

	def test_03_generate_text_no_api_key(self):
		"""Test generate_text when API key missing"""
		from frappe.utils.password import set_encrypted_password

		set_encrypted_password(
			"AI Provider", "AI Provider", "",
			fieldname="api_key"
		)
		frappe.db.commit()

		result = generate_text("Test prompt")

		self.assertIn("api key", result.lower())

	@patch('ai_assistant.ai_provider_wrapper.AIProviderResolver')
	def test_04_generate_text_with_context(self, mock_resolver_class):
		"""Test generate_text with context parameter"""
		mock_resolver = MagicMock()
		mock_resolver.call_ai_api.return_value = "Response with context"
		mock_resolver_class.return_value = mock_resolver

		result = generate_text("Test prompt", context={"key": "value"})

		self.assertEqual(result, "Response with context")
		# Verify context was passed
		call_args = mock_resolver.call_ai_api.call_args
		self.assertEqual(call_args.kwargs.get("context"), {"key": "value"})

	@patch('ai_assistant.ai_provider_wrapper.AIProviderResolver')
	def test_05_generate_text_with_system_message(self, mock_resolver_class):
		"""Test generate_text with system message"""
		mock_resolver = MagicMock()
		mock_resolver.call_ai_api.return_value = "Custom system response"
		mock_resolver_class.return_value = mock_resolver

		result = generate_text("Test prompt", system_message="Be helpful")

		self.assertEqual(result, "Custom system response")
		call_args = mock_resolver.call_ai_api.call_args
		self.assertEqual(call_args.kwargs.get("system_message"), "Be helpful")

	@patch('ai_assistant.ai_provider_wrapper.AIProviderResolver')
	def test_06_generate_text_api_error(self, mock_resolver_class):
		"""Test generate_text handles API errors gracefully"""
		mock_resolver = MagicMock()
		mock_resolver.call_ai_api.side_effect = Exception("API Error")
		mock_resolver_class.return_value = mock_resolver

		result = generate_text("Test prompt")

		# Should return error message, not raise exception
		self.assertIn("failed", result.lower())

	@patch('ai_assistant.ai_provider_wrapper.AIProviderResolver')
	def test_07_generate_text_permission_error(self, mock_resolver_class):
		"""Test generate_text handles permission errors"""
		mock_resolver = MagicMock()
		mock_resolver.call_ai_api.side_effect = frappe.PermissionError("No access")
		mock_resolver_class.return_value = mock_resolver

		result = generate_text("Test prompt")

		self.assertIn("permission", result.lower())

	@patch('ai_assistant.ai_provider_wrapper.AIProviderResolver')
	def test_08_call_ai_alias(self, mock_resolver_class):
		"""Test call_ai is alias for generate_text"""
		mock_resolver = MagicMock()
		mock_resolver.call_ai_api.return_value = "Alias response"
		mock_resolver_class.return_value = mock_resolver

		result = call_ai("Test prompt")

		self.assertEqual(result, "Alias response")

	def test_09_generate_text_provider_not_exists(self):
		"""Test generate_text when AI Provider doesn't exist"""
		# This shouldn't happen in normal operation, but test graceful handling
		with patch('ai_assistant.ai_provider_wrapper.frappe.db.exists', return_value=False):
			result = generate_text("Test prompt")

		self.assertIn("not configured", result.lower())

	@patch('ai_assistant.ai_provider_wrapper.AIProviderResolver')
	def test_10_generate_text_uses_default_model(self, mock_resolver_class):
		"""Test generate_text uses provider's default model"""
		mock_resolver = MagicMock()
		mock_resolver.call_ai_api.return_value = "Response"
		mock_resolver_class.return_value = mock_resolver

		generate_text("Test prompt")

		call_args = mock_resolver.call_ai_api.call_args
		self.assertEqual(call_args.kwargs.get("model"), "gpt-4o-mini")

