"""
Test AI Provider Resolver

Tests centralized AI Provider configuration resolver
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ai_assistant.ai_provider_resolver import (
	AIProviderResolver,
	call_ai,
	get_ai_config,
	validate_ai_setup,
)


class TestAIProviderResolver(unittest.TestCase):
	"""
	Test AIProviderResolver class

	Test Coverage:
	- get_ai_provider_config() - configuration retrieval
	- get_api_credentials() - credential retrieval
	- call_ai_api() - API calls
	- validate_configuration() - configuration validation
	- Permission checks
	- Error handling
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
		self.provider.api_key = "test_api_key_resolver"
		self.provider.api_base_url = "https://api.openai.com/v1"
		self.provider.default_model = "gpt-4o-mini"
		self.provider.is_active = 1
		self.provider.save()
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	def test_01_get_ai_provider_config(self):
		"""Test get_ai_provider_config returns configuration"""
		config = AIProviderResolver.get_ai_provider_config()

		self.assertIsNotNone(config)
		self.assertEqual(config["provider"], "OpenAI")
		self.assertEqual(config["default_model"], "gpt-4o-mini")
		self.assertEqual(config["api_base_url"], "https://api.openai.com/v1")
		self.assertTrue(config["is_active"])

	def test_02_get_ai_provider_config_api_key_status(self):
		"""Test config returns API key status, not actual key"""
		config = AIProviderResolver.get_ai_provider_config()

		self.assertIn("api_key_status", config)
		self.assertEqual(config["api_key_status"], "SET")
		# Should NOT contain actual API key
		self.assertNotIn("api_key", config)

	def test_03_get_ai_provider_config_permission_check(self):
		"""Test config requires permission"""
		frappe.set_user("Guest")

		with self.assertRaises(frappe.PermissionError):
			AIProviderResolver.get_ai_provider_config()

		frappe.set_user("Administrator")

	def test_04_get_api_credentials_success(self):
		"""Test credential retrieval"""
		api_key, base_url, provider = AIProviderResolver.get_api_credentials()

		self.assertIsNotNone(api_key)
		self.assertEqual(base_url, "https://api.openai.com/v1")
		self.assertEqual(provider, "OpenAI")

	def test_05_get_api_credentials_inactive(self):
		"""Test credentials fail when provider inactive"""
		self.provider.is_active = 0
		self.provider.save()
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError):
			AIProviderResolver.get_api_credentials()

	def test_06_get_api_credentials_no_api_key(self):
		"""Test credentials fail when API key missing"""
		from frappe.utils.password import set_encrypted_password

		set_encrypted_password(
			"AI Provider", "AI Provider", "",
			fieldname="api_key"
		)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as context:
			AIProviderResolver.get_api_credentials()

		self.assertIn("api key", str(context.exception).lower())

	def test_07_get_api_credentials_permission_check(self):
		"""Test credentials require write permission"""
		frappe.set_user("Guest")

		with self.assertRaises(frappe.PermissionError):
			AIProviderResolver.get_api_credentials()

		frappe.set_user("Administrator")

	@patch('ai_assistant.ai_provider_resolver.requests.post')
	def test_08_call_ai_api_success(self, mock_post):
		"""Test successful AI API call"""
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Test response"}}]
		}
		mock_post.return_value = mock_response

		result = AIProviderResolver.call_ai_api("Test prompt")

		self.assertEqual(result, "Test response")
		mock_post.assert_called_once()

	@patch('ai_assistant.ai_provider_resolver.requests.post')
	def test_09_call_ai_api_with_context(self, mock_post):
		"""Test AI API call with context"""
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Response with context"}}]
		}
		mock_post.return_value = mock_response

		context = {"document": "Sales Invoice", "amount": 1000}
		result = AIProviderResolver.call_ai_api("Analyze this", context=context)

		self.assertEqual(result, "Response with context")

		# Verify context was included in request
		call_args = mock_post.call_args
		request_body = call_args[1]["json"]
		messages = request_body["messages"]

		# Should have system, context, and user messages
		self.assertGreaterEqual(len(messages), 3)

	@patch('ai_assistant.ai_provider_resolver.requests.post')
	def test_10_call_ai_api_timeout(self, mock_post):
		"""Test AI API handles timeout"""
		import requests
		mock_post.side_effect = requests.exceptions.Timeout()

		with self.assertRaises(frappe.ValidationError) as context:
			AIProviderResolver.call_ai_api("Test prompt")

		self.assertIn("timed out", str(context.exception).lower())

	def test_11_call_ai_api_permission_check(self):
		"""Test AI API requires permission"""
		frappe.set_user("Guest")

		with self.assertRaises(frappe.PermissionError):
			AIProviderResolver.call_ai_api("Test prompt")

		frappe.set_user("Administrator")

	def test_12_validate_configuration_complete(self):
		"""Test validation with complete configuration"""
		# Skip connection test by mocking
		with patch.object(AIProviderResolver, 'call_ai_api', return_value="Success"):
			result = AIProviderResolver.validate_configuration()

		self.assertTrue(result["provider_configured"])
		self.assertTrue(result["api_key_configured"])
		self.assertTrue(result["model_configured"])

	def test_13_validate_configuration_incomplete(self):
		"""Test validation with incomplete configuration"""
		# Clear provider
		self.provider.provider = ""
		# Need to skip mandatory for this test
		self.provider.flags.ignore_mandatory = True
		self.provider.save()
		frappe.db.commit()

		result = AIProviderResolver.validate_configuration()

		self.assertFalse(result["provider_configured"])
		self.assertIn("Provider not configured", result["errors"])

	def test_14_validate_configuration_permission_check(self):
		"""Test validation requires write permission"""
		frappe.set_user("Guest")

		with self.assertRaises(frappe.PermissionError):
			AIProviderResolver.validate_configuration()

		frappe.set_user("Administrator")

	def test_15_shorthand_get_ai_config(self):
		"""Test shorthand get_ai_config function"""
		config = get_ai_config()

		self.assertIsNotNone(config)
		self.assertIn("provider", config)

	@patch('ai_assistant.ai_provider_resolver.requests.post')
	def test_16_shorthand_call_ai(self, mock_post):
		"""Test shorthand call_ai function"""
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Shorthand response"}}]
		}
		mock_post.return_value = mock_response

		result = call_ai("Test prompt")

		self.assertEqual(result, "Shorthand response")

	@patch('ai_assistant.ai_provider_resolver.requests.post')
	def test_17_shorthand_call_ai_with_json_context(self, mock_post):
		"""Test call_ai with JSON string context"""
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Response"}}]
		}
		mock_post.return_value = mock_response

		import json
		context = json.dumps({"key": "value"})
		result = call_ai("Test", context=context)

		self.assertEqual(result, "Response")

	@patch('ai_assistant.ai_provider_resolver.requests.post')
	def test_18_shorthand_call_ai_with_text_context(self, mock_post):
		"""Test call_ai with plain text context"""
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Response"}}]
		}
		mock_post.return_value = mock_response

		result = call_ai("Test", context="Plain text context")

		self.assertEqual(result, "Response")

	def test_19_validate_ai_setup_shorthand(self):
		"""Test shorthand validate_ai_setup function"""
		with patch.object(AIProviderResolver, 'call_ai_api', return_value="Success"):
			result = validate_ai_setup()

		self.assertIn("provider_configured", result)
		self.assertIn("status", result)

	def test_20_check_api_key_status_error_handling(self):
		"""Test _check_api_key_status handles errors"""
		# This is an internal method, test via get_ai_provider_config
		config = AIProviderResolver.get_ai_provider_config()
		# Should return a valid status even in edge cases
		self.assertIn(config["api_key_status"], ["SET", "NOT_SET", "ERROR"])

