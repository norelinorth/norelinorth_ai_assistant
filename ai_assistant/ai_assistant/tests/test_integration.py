"""
Test End-to-End Integration Workflows

Tests complete workflows from configuration to AI calls with observability
"""
import json
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ai_assistant.ai_observability import (
	LANGFUSE_AVAILABLE,
	get_langfuse_client,
	reset_langfuse_client,
	validate_langfuse_config,
)
from ai_assistant.ai_provider_api import call_ai, get_ai_config, validate_ai_config


class TestIntegration(unittest.TestCase):
	"""
	Test end-to-end integration workflows

	Test Coverage:
	- Complete AI call workflow without Langfuse
	- Complete AI call workflow with Langfuse tracing
	- Configuration changes and cache reset
	- Multi-provider scenarios
	- Error recovery flows
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

	def setUp(self):
		"""Set up before each test"""
		frappe.db.rollback()
		reset_langfuse_client()

		# Configure AI Provider
		self.provider = frappe.get_single("AI Provider")
		self.provider.provider = "OpenAI"
		self.provider.api_key = "test_api_key_12345"
		self.provider.api_base_url = "https://api.openai.com/v1"
		self.provider.default_model = "gpt-4o-mini"
		self.provider.is_active = 1
		self.provider.enable_langfuse = 0

		self.provider.save()
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after each test"""
		reset_langfuse_client()
		frappe.db.rollback()

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_01_complete_workflow_without_tracing(self, mock_post):
		"""Test complete AI call workflow without Langfuse tracing"""
		# Mock successful API response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "AI response without tracing"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
		}
		mock_post.return_value = mock_response

		# Step 1: Validate configuration
		config = get_ai_config()
		self.assertEqual(config["provider"], "OpenAI")
		self.assertTrue(config["is_active"])

		validation = validate_ai_config()
		self.assertTrue(validation["configured"])
		self.assertTrue(validation["active"])

		# Step 2: Verify Langfuse is disabled
		langfuse_validation = validate_langfuse_config()
		self.assertEqual(langfuse_validation["status"], "disabled")

		# Step 3: Make AI call
		response = call_ai("What is 2+2?")

		# Verify response
		self.assertEqual(response, "AI response without tracing")

		# Verify API was called
		mock_post.assert_called_once()

	@patch('ai_assistant.ai_observability.Langfuse')
	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_02_complete_workflow_with_tracing(self, mock_post, mock_langfuse_class):
		"""Test complete AI call workflow with Langfuse tracing"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Configure Langfuse
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_secret_key = "sk-lf-test-secret"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		self.provider.save()
		frappe.db.commit()

		# Mock Langfuse client
		mock_langfuse_instance = MagicMock()
		mock_generation = MagicMock()
		mock_generation.__enter__ = MagicMock(return_value=mock_generation)
		mock_generation.__exit__ = MagicMock(return_value=False)
		mock_langfuse_instance.start_as_current_generation.return_value = mock_generation
		mock_langfuse_class.return_value = mock_langfuse_instance

		# Mock AI API response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "AI response with tracing"}}],
			"usage": {"prompt_tokens": 15, "completion_tokens": 10, "total_tokens": 25}
		}
		mock_post.return_value = mock_response

		# Step 1: Validate Langfuse configuration
		langfuse_validation = validate_langfuse_config()
		self.assertEqual(langfuse_validation["status"], "active")
		self.assertTrue(langfuse_validation["configured"])

		# Step 2: Get Langfuse client
		client = get_langfuse_client()
		self.assertIsNotNone(client)

		# Step 3: Make AI call (should use Langfuse tracing)
		response = call_ai("Analyze this data", context=json.dumps({"value": 100}))

		# Verify response
		self.assertEqual(response, "AI response with tracing")

		# Verify Langfuse tracing was used
		mock_langfuse_instance.start_as_current_generation.assert_called_once()

		# Verify generation.update was called
		mock_generation.update.assert_called_once()

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_03_provider_change_workflow(self, mock_post):
		"""Test changing provider (OpenAI → Anthropic)"""
		# Mock response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Response from Anthropic"}}],
			"usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}
		}
		mock_post.return_value = mock_response

		# Step 1: Start with OpenAI
		config = get_ai_config()
		self.assertEqual(config["provider"], "OpenAI")

		# Step 2: Change to Anthropic
		self.provider.provider = "Anthropic"
		self.provider.api_base_url = "https://api.anthropic.com/v1"
		self.provider.default_model = "claude-3-sonnet-20240229"
		self.provider.save()
		frappe.db.commit()

		# Step 3: Verify configuration updated
		config = get_ai_config()
		self.assertEqual(config["provider"], "Anthropic")
		self.assertEqual(config["api_base_url"], "https://api.anthropic.com/v1")
		self.assertEqual(config["default_model"], "claude-3-sonnet-20240229")

		# Step 4: Make AI call with new provider
		response = call_ai("Hello")
		self.assertEqual(response, "Response from Anthropic")

		# Verify correct URL was called
		call_args = mock_post.call_args
		self.assertIn("https://api.anthropic.com/v1", call_args[0][0])

	@patch('ai_assistant.ai_observability.Langfuse')
	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_04_enable_disable_langfuse_workflow(self, mock_post, mock_langfuse_class):
		"""Test enabling and disabling Langfuse during runtime"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Mock API response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Test response"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
		}
		mock_post.return_value = mock_response

		# Mock Langfuse
		mock_langfuse_instance = MagicMock()
		mock_generation = MagicMock()
		mock_generation.__enter__ = MagicMock(return_value=mock_generation)
		mock_generation.__exit__ = MagicMock(return_value=False)
		mock_langfuse_instance.start_as_current_generation.return_value = mock_generation
		mock_langfuse_class.return_value = mock_langfuse_instance

		# Step 1: Langfuse disabled
		validation = validate_langfuse_config()
		self.assertEqual(validation["status"], "disabled")

		# Make call without tracing
		call_ai("Test 1")
		mock_langfuse_class.assert_not_called()

		# Step 2: Enable Langfuse
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test"
		self.provider.langfuse_secret_key = "sk-lf-secret"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		self.provider.save()
		frappe.db.commit()

		# Reset cache to pick up new config
		reset_langfuse_client()

		# Step 3: Verify Langfuse is now active
		validation = validate_langfuse_config()
		self.assertEqual(validation["status"], "active")

		# Make call with tracing
		call_ai("Test 2")
		mock_langfuse_class.assert_called()

		# Step 4: Disable Langfuse again
		self.provider.enable_langfuse = 0
		self.provider.save()
		frappe.db.commit()

		reset_langfuse_client()

		# Verify disabled
		validation = validate_langfuse_config()
		self.assertEqual(validation["status"], "disabled")

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_05_error_recovery_workflow(self, mock_post):
		"""Test error recovery: API error → fix config → retry"""
		# Step 1: First call fails (401 unauthorized)
		import requests
		mock_response_401 = MagicMock()
		mock_response_401.status_code = 401
		mock_post.return_value = mock_response_401
		mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(
			response=mock_response_401
		)

		# Should fail with API key error
		with self.assertRaises(Exception) as context:
			call_ai("Test")
		self.assertIn("api key", str(context.exception).lower())

		# Step 2: Fix API key
		self.provider.api_key = "new_correct_api_key"
		self.provider.save()
		frappe.db.commit()

		# Step 3: Retry with correct key (mock success)
		mock_response_success = MagicMock()
		mock_response_success.status_code = 200
		mock_response_success.json.return_value = {
			"choices": [{"message": {"content": "Success after fix"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
		}
		mock_post.return_value = mock_response_success
		mock_post.return_value.raise_for_status.side_effect = None

		# Should now succeed
		response = call_ai("Test retry")
		self.assertEqual(response, "Success after fix")

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_06_model_override_workflow(self, mock_post):
		"""Test using default model vs custom model override"""
		# Mock response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Model response"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
		}
		mock_post.return_value = mock_response

		# Step 1: Call with default model
		call_ai("Test default model")

		# Verify default model was used
		body = mock_post.call_args[1]["json"]
		self.assertEqual(body["model"], "gpt-4o-mini")

		# Step 2: Call with custom model
		call_ai("Test custom model", model="gpt-4-turbo")

		# Verify custom model was used
		body = mock_post.call_args[1]["json"]
		self.assertEqual(body["model"], "gpt-4-turbo")

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_07_context_handling_workflow(self, mock_post):
		"""Test various context formats (JSON, plain text, None)"""
		# Mock response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Context response"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
		}
		mock_post.return_value = mock_response

		# Step 1: No context
		call_ai("Test without context")
		body = mock_post.call_args[1]["json"]
		messages = body["messages"]
		# Should have system message and user message only
		self.assertEqual(len([m for m in messages if m["role"] == "user"]), 1)

		# Step 2: JSON context
		context_json = {"doctype": "Journal Entry", "amount": 1000}
		call_ai("Test with JSON context", context=json.dumps(context_json))
		body = mock_post.call_args[1]["json"]
		messages = body["messages"]
		# Should have additional context message
		context_found = any("Context:" in m.get("content", "") for m in messages)
		self.assertTrue(context_found)

		# Step 3: Plain text context
		call_ai("Test with plain text", context="This is plain text")
		body = mock_post.call_args[1]["json"]
		messages = body["messages"]
		context_found = any("Context:" in m.get("content", "") for m in messages)
		self.assertTrue(context_found)

	@patch('ai_assistant.ai_observability.Langfuse')
	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_08_langfuse_failure_fallback_workflow(self, mock_post, mock_langfuse_class):
		"""Test graceful degradation when Langfuse tracing fails"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Enable Langfuse
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test"
		self.provider.langfuse_secret_key = "sk-lf-secret"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		self.provider.save()
		frappe.db.commit()

		# Mock Langfuse to fail during tracing
		mock_langfuse_instance = MagicMock()
		mock_generation = MagicMock()
		mock_generation.__enter__ = MagicMock(side_effect=Exception("Langfuse connection failed"))
		mock_langfuse_instance.start_as_current_generation.return_value = mock_generation
		mock_langfuse_class.return_value = mock_langfuse_instance

		# Mock successful AI API response (for retry without tracing)
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Response without tracing"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
		}
		mock_post.return_value = mock_response

		# Should gracefully degrade to no tracing and still return AI response
		response = call_ai("Test with Langfuse failure")

		# Should get response despite Langfuse failure
		self.assertEqual(response, "Response without tracing")

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_09_inactive_to_active_workflow(self, mock_post):
		"""Test activating an inactive provider"""
		# Step 1: Deactivate provider
		self.provider.is_active = 0
		self.provider.save()
		frappe.db.commit()

		# Verify inactive
		validation = validate_ai_config()
		self.assertFalse(validation["active"])

		# Should fail to make AI call
		with self.assertRaises(Exception) as context:
			call_ai("Test")
		self.assertIn("not active", str(context.exception).lower())

		# Step 2: Activate provider
		self.provider.is_active = 1
		self.provider.save()
		frappe.db.commit()

		# Verify active
		validation = validate_ai_config()
		self.assertTrue(validation["active"])

		# Step 3: Should now succeed
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Success after activation"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
		}
		mock_post.return_value = mock_response

		response = call_ai("Test after activation")
		self.assertEqual(response, "Success after activation")

	@patch('ai_assistant.ai_provider_api.requests.post')
	def test_10_azure_openai_integration_workflow(self, mock_post):
		"""Test complete workflow with Azure OpenAI configuration"""
		# Configure for Azure OpenAI
		self.provider.provider = "Azure OpenAI"
		self.provider.api_base_url = "https://test-resource.openai.azure.com/openai/deployments/gpt-4"
		self.provider.default_model = "gpt-4"
		self.provider.save()
		frappe.db.commit()

		# Mock response
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"choices": [{"message": {"content": "Azure response"}}],
			"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
		}
		mock_post.return_value = mock_response

		# Verify configuration
		config = get_ai_config()
		self.assertEqual(config["provider"], "Azure OpenAI")
		self.assertIn("azure", config["api_base_url"].lower())

		# Make call
		response = call_ai("Test Azure")
		self.assertEqual(response, "Azure response")

		# Verify correct Azure URL was used
		call_args = mock_post.call_args
		self.assertIn("azure", call_args[0][0].lower())
