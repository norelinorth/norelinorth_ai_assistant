"""
Test AI Provider API

Tests API functions for AI provider integration
"""
import json
import unittest
from unittest.mock import MagicMock, patch

import frappe
from frappe.utils.password import set_encrypted_password

from ai_assistant.ai_provider_api import call_ai, get_ai_config, validate_ai_config


class TestAIProviderAPI(unittest.TestCase):
	"""
	Test AI Provider API functions

	Test Coverage:
	- get_ai_config() function
	- call_ai() function with various scenarios
	- validate_ai_config() function
	- Permission checks
	- Error handling
	- Configuration validation
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

	def setUp(self):
		"""Set up before each test"""
		frappe.db.rollback()

		# Ensure we're Administrator for setup
		frappe.set_user("Administrator")

		# Configure AI Provider for tests
		self.provider = frappe.get_single("AI Provider")
		self.provider.provider = "OpenAI"
		self.provider.api_key = "test_api_key_12345"
		self.provider.api_base_url = "https://api.openai.com/v1"
		self.provider.default_model = "gpt-4o-mini"
		self.provider.is_active = 1

		self.provider.save()
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	def test_01_get_ai_config(self):
		"""Test get_ai_config() returns configuration"""
		config = get_ai_config()

		self.assertIsNotNone(config)
		self.assertEqual(config["provider"], "OpenAI")
		self.assertEqual(config["api_base_url"], "https://api.openai.com/v1")
		self.assertEqual(config["default_model"], "gpt-4o-mini")
		self.assertEqual(config["is_active"], True)

	def test_02_get_ai_config_api_key_status(self):
		"""Test get_ai_config() doesn't expose API key"""
		config = get_ai_config()

		# Should have api_key_status but NOT the actual key
		self.assertIn("api_key_status", config)
		self.assertEqual(config["api_key_status"], "SET")
		self.assertNotIn("api_key", config)

	def test_03_get_ai_config_no_api_key(self):
		"""Test get_ai_config() when API key is not set"""
		# Clear API key
		set_encrypted_password(
			"AI Provider", "AI Provider", "",
			fieldname="api_key"
		)
		frappe.db.commit()

		config = get_ai_config()

		self.assertEqual(config["api_key_status"], "NOT_SET")

	def test_04_validate_ai_config_complete(self):
		"""Test validate_ai_config() with complete configuration"""
		result = validate_ai_config()

		self.assertIsNotNone(result)
		self.assertTrue(result["configured"])
		self.assertTrue(result["active"])

	def test_05_validate_ai_config_inactive(self):
		"""Test validate_ai_config() when provider is inactive"""
		# Disable provider
		self.provider.is_active = 0
		self.provider.save()
		frappe.db.commit()

		result = validate_ai_config()

		self.assertTrue(result["configured"])
		self.assertFalse(result["active"])

	def test_06_validate_ai_config_no_api_key(self):
		"""Test validate_ai_config() when API key is missing"""
		# Clear API key
		set_encrypted_password(
			"AI Provider", "AI Provider", "",
			fieldname="api_key"
		)
		frappe.db.commit()

		result = validate_ai_config()

		self.assertFalse(result["configured"])

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_07_call_ai_success(self, mock_post):
		"""Test call_ai() with successful API response"""
		# Mock successful API response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [
				{
					"message": {
						"content": "This is a test AI response"
					}
				}
			],
			"usage": {
				"prompt_tokens": 10,
				"completion_tokens": 8,
				"total_tokens": 18
			}
		}
		mock_post.return_value = mock_response

		# Call AI
		response = call_ai("What is 2+2?")

		# Verify response
		self.assertEqual(response, "This is a test AI response")

		# Verify API was called correctly
		mock_post.assert_called_once()
		call_args = mock_post.call_args

		# Check URL
		self.assertIn("https://api.openai.com/v1/chat/completions", call_args[0])

		# Check headers
		headers = call_args[1]["headers"]
		self.assertEqual(headers["Content-Type"], "application/json")
		self.assertIn("Bearer", headers["Authorization"])

		# Check request body
		body = call_args[1]["json"]
		self.assertEqual(body["model"], "gpt-4o-mini")
		self.assertEqual(body["temperature"], 0.7)
		self.assertEqual(body["max_tokens"], 2000)
		self.assertIn("messages", body)

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_08_call_ai_with_context(self, mock_post):
		"""Test call_ai() with context parameter"""
		# Mock response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Response with context"}}],
			"usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
		}
		mock_post.return_value = mock_response

		# Call with context
		context = {"document": "Journal Entry", "amount": 1000}
		response = call_ai("Analyze this", context=json.dumps(context))

		# Verify response
		self.assertEqual(response, "Response with context")

		# Verify context was included in messages
		body = mock_post.call_args[1]["json"]
		messages = body["messages"]

		# Should have system message, context message, and user message
		self.assertGreaterEqual(len(messages), 3)

		# Check that context was included
		context_found = False
		for msg in messages:
			if "Context:" in msg.get("content", ""):
				context_found = True
				break
		self.assertTrue(context_found, "Context not found in messages")

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_09_call_ai_with_model_override(self, mock_post):
		"""Test call_ai() with model parameter override"""
		# Mock response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Response from custom model"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
		}
		mock_post.return_value = mock_response

		# Call with custom model
		response = call_ai("Test prompt", model="gpt-4-turbo")

		# Verify custom model was used
		body = mock_post.call_args[1]["json"]
		self.assertEqual(body["model"], "gpt-4-turbo")

	def test_10_call_ai_inactive_provider(self):
		"""Test call_ai() fails when provider is inactive"""
		# Disable provider
		self.provider.is_active = 0
		self.provider.save()
		frappe.db.commit()

		# Should fail
		with self.assertRaises(Exception) as context:
			call_ai("Test prompt")

		self.assertIn("not active", str(context.exception).lower())

	def test_11_call_ai_missing_api_key(self):
		"""Test call_ai() fails when API key is missing"""
		# Clear API key
		set_encrypted_password(
			"AI Provider", "AI Provider", "",
			fieldname="api_key"
		)
		frappe.db.commit()

		# Should fail
		with self.assertRaises(Exception) as context:
			call_ai("Test prompt")

		self.assertIn("api key", str(context.exception).lower())

	def test_12_call_ai_missing_base_url(self):
		"""Test call_ai() fails when API base URL is missing (no hardcoded fallback)"""
		# Clear base URL - should fail to save since it's required
		with self.assertRaises(frappe.exceptions.MandatoryError):
			self.provider.api_base_url = ""
			self.provider.save()
			frappe.db.commit()

	def test_13_call_ai_missing_default_model(self):
		"""Test call_ai() fails when default model is missing and no model provided"""
		# Clear default model - should fail to save since it's required
		with self.assertRaises(frappe.exceptions.MandatoryError):
			self.provider.default_model = ""
			self.provider.save()
			frappe.db.commit()

	def test_14_model_override_replaces_default(self):
		"""Test that model parameter overrides default model"""
		# Now that default_model is required, test that override still works
		# Mock response
		with patch('ai_assistant.ai_provider_api.requests.post') as mock_post:
			mock_response = MagicMock()
			mock_response.status_code = 200
			mock_response.json.return_value = {
				"choices": [{"message": {"content": "Success"}}],
				"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
			}
			mock_post.return_value = mock_response

			# Call with custom model (should override default "gpt-4o-mini")
			response = call_ai("Test", model="gpt-4-turbo")

			# Verify custom model was used
			body = mock_post.call_args[1]["json"]
			self.assertEqual(body["model"], "gpt-4-turbo")

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_15_call_ai_timeout(self, mock_post):
		"""Test call_ai() handles timeout errors"""
		# Mock timeout
		import requests
		mock_post.side_effect = requests.exceptions.Timeout()

		# Should fail with timeout error
		with self.assertRaises(Exception) as context:
			call_ai("Test prompt")

		# Message is "AI API request timed out"
		error_msg = str(context.exception).lower()
		self.assertTrue("timeout" in error_msg or "timed out" in error_msg)

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_16_call_ai_http_401_unauthorized(self, mock_post):
		"""Test call_ai() handles 401 unauthorized errors"""
		# Mock 401 error
		import requests
		mock_response = MagicMock()
		mock_response.status_code = 401
		mock_post.return_value = mock_response
		mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

		# Should fail with API key error
		with self.assertRaises(Exception) as context:
			call_ai("Test prompt")

		self.assertIn("api key", str(context.exception).lower())

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_17_call_ai_http_429_rate_limit(self, mock_post):
		"""Test call_ai() handles 429 rate limit errors"""
		# Mock 429 error
		import requests
		mock_response = MagicMock()
		mock_response.status_code = 429
		mock_post.return_value = mock_response
		mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

		# Should fail with rate limit error
		with self.assertRaises(Exception) as context:
			call_ai("Test prompt")

		self.assertIn("rate limit", str(context.exception).lower())

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_18_call_ai_invalid_response(self, mock_post):
		"""Test call_ai() handles invalid API responses"""
		# Mock invalid response (no choices)
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {"error": "something went wrong"}
		mock_post.return_value = mock_response

		# Should fail with error (either "invalid response" or "failed to call AI API")
		with self.assertRaises(Exception) as context:
			call_ai("Test prompt")

		error_msg = str(context.exception).lower()
		self.assertTrue("invalid" in error_msg or "failed" in error_msg)

	def test_19_permission_checks(self):
		"""Test API functions check permissions"""
		# Set user without permissions
		frappe.set_user("Guest")

		# All API functions should fail with permission error (frappe.throw raises ValidationError)
		with self.assertRaises(Exception):  # frappe.throw raises ValidationError
			get_ai_config()

		with self.assertRaises(Exception):
			validate_ai_config()

		with self.assertRaises(Exception):
			call_ai("Test")

		# Reset to Administrator
		frappe.set_user("Administrator")

	def test_20_context_plain_text(self):
		"""Test call_ai() handles plain text context (not JSON)"""
		with patch('ai_assistant.ai_provider_api.requests.post') as mock_post:
			mock_response = MagicMock()
			mock_response.status_code = 200
			mock_response.json.return_value = {
				"choices": [{"message": {"content": "Response"}}],
				"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
			}
			mock_post.return_value = mock_response

			# Call with plain text context
			response = call_ai("Test", context="This is plain text context")

			# Should work - context will be wrapped in {"text": ...}
			self.assertEqual(response, "Response")

			# Verify context was included
			body = mock_post.call_args[1]["json"]
			messages = body["messages"]

			context_found = False
			for msg in messages:
				if "Context:" in msg.get("content", ""):
					context_found = True
					break
			self.assertTrue(context_found)
