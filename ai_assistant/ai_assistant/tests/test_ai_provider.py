"""
Test AI Provider DocType

Tests configuration, validation, and field requirements for AI Provider
"""
import unittest

import frappe


class TestAIProvider(unittest.TestCase):
	"""
	Test AI Provider DocType configuration and validation

	Test Coverage:
	- AI Provider singleton creation
	- Required field validation
	- Provider name extensibility
	- API configuration
	- Langfuse settings
	- Active/inactive status
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

	def setUp(self):
		"""Set up before each test"""
		# Start with clean slate
		frappe.db.rollback()

		# Get AI Provider singleton
		self.provider = frappe.get_single("AI Provider")

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	def test_01_ai_provider_exists(self):
		"""Test AI Provider singleton exists"""
		provider = frappe.get_single("AI Provider")
		self.assertIsNotNone(provider)
		self.assertEqual(provider.doctype, "AI Provider")

	def test_02_required_fields(self):
		"""Test required fields are enforced"""
		provider = frappe.get_single("AI Provider")

		# Clear all fields
		provider.provider = ""
		provider.api_key = ""
		provider.api_base_url = ""
		provider.default_model = ""

		# Should fail validation due to required fields
		with self.assertRaises(frappe.exceptions.MandatoryError):
			provider.save()

	def test_03_provider_name_extensibility(self):
		"""Test provider field accepts any text (not limited to dropdown)"""
		provider = frappe.get_single("AI Provider")

		# Test various provider names (should all work - Data field, not Select)
		test_providers = [
			"OpenAI",
			"Anthropic",
			"Azure OpenAI",
			"Google AI",
			"Local LLaMA",
			"Custom Provider"
		]

		for provider_name in test_providers:
			provider.provider = provider_name
			provider.api_key = "test_key"
			provider.api_base_url = "https://api.example.com/v1"
			provider.default_model = "test-model"

			# Should not raise any error
			provider.save()

			# Verify it was saved
			self.assertEqual(provider.provider, provider_name)

	def test_04_api_base_url_required(self):
		"""Test API Base URL is required (no hardcoded fallback)"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "OpenAI"
		provider.api_key = "test_key"
		provider.default_model = "gpt-4o-mini"
		provider.api_base_url = ""  # Empty - should fail

		with self.assertRaises(frappe.exceptions.MandatoryError):
			provider.save()

	def test_05_default_model_required(self):
		"""Test Default Model is required (no hardcoded fallback)"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "OpenAI"
		provider.api_key = "test_key"
		provider.api_base_url = "https://api.openai.com/v1"
		provider.default_model = ""  # Empty - should fail

		with self.assertRaises(frappe.exceptions.MandatoryError):
			provider.save()

	def test_06_api_key_required(self):
		"""Test API Key is required"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "OpenAI"
		provider.api_base_url = "https://api.openai.com/v1"
		provider.default_model = "gpt-4o-mini"
		provider.api_key = ""  # Empty - should fail

		with self.assertRaises(frappe.exceptions.MandatoryError):
			provider.save()

	def test_07_valid_configuration_openai(self):
		"""Test valid OpenAI configuration"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "OpenAI"
		provider.api_key = "test_api_key_12345"
		provider.api_base_url = "https://api.openai.com/v1"
		provider.default_model = "gpt-4o-mini"
		provider.is_active = 1

		# Should save successfully
		provider.save()

		# Verify saved values
		self.assertEqual(provider.provider, "OpenAI")
		self.assertEqual(provider.api_base_url, "https://api.openai.com/v1")
		self.assertEqual(provider.default_model, "gpt-4o-mini")
		self.assertEqual(provider.is_active, 1)

	def test_08_valid_configuration_anthropic(self):
		"""Test valid Anthropic configuration (tests extensibility)"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "Anthropic"
		provider.api_key = "test_anthropic_key"
		provider.api_base_url = "https://api.anthropic.com/v1"
		provider.default_model = "claude-3-sonnet-20240229"
		provider.is_active = 1

		# Should save successfully
		provider.save()

		# Verify saved values
		self.assertEqual(provider.provider, "Anthropic")
		self.assertEqual(provider.api_base_url, "https://api.anthropic.com/v1")
		self.assertEqual(provider.default_model, "claude-3-sonnet-20240229")

	def test_09_langfuse_disabled_by_default(self):
		"""Test Langfuse default value in DocType definition"""
		# Check DocType meta default value (not current DB value which may have been changed by other tests)
		from frappe import get_meta
		meta = get_meta("AI Provider")
		enable_langfuse_field = next((f for f in meta.fields if f.fieldname == "enable_langfuse"), None)

		self.assertIsNotNone(enable_langfuse_field)
		# Default should be "0" (disabled) as per DocType JSON
		self.assertEqual(enable_langfuse_field.default, "0")

	def test_10_langfuse_configuration(self):
		"""Test Langfuse configuration fields"""
		provider = frappe.get_single("AI Provider")

		# Configure required AI Provider fields
		provider.provider = "OpenAI"
		provider.api_key = "test_api_key"
		provider.api_base_url = "https://api.openai.com/v1"
		provider.default_model = "gpt-4o-mini"

		# Configure Langfuse
		provider.enable_langfuse = 1
		provider.langfuse_public_key = "pk-lf-test-12345"
		provider.langfuse_secret_key = "sk-lf-test-secret"
		provider.langfuse_host = "https://cloud.langfuse.com"

		# Should save successfully
		provider.save()

		# Verify Langfuse settings
		self.assertEqual(provider.enable_langfuse, 1)
		self.assertEqual(provider.langfuse_public_key, "pk-lf-test-12345")
		self.assertEqual(provider.langfuse_host, "https://cloud.langfuse.com")

	def test_11_langfuse_default_host(self):
		"""Test Langfuse host has correct default"""
		provider = frappe.get_single("AI Provider")

		# Check default value from DocType definition
		# Note: Default is set in DocType JSON, not in Python code (standards compliant)
		self.assertIsNotNone(provider.langfuse_host)
		self.assertEqual(provider.langfuse_host, "https://cloud.langfuse.com")

	def test_12_is_active_default(self):
		"""Test is_active defaults to True"""
		provider = frappe.get_single("AI Provider")

		# Default should be active
		self.assertEqual(provider.is_active, 1)

	def test_13_extra_headers_json(self):
		"""Test extra_headers field accepts JSON"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "OpenAI"
		provider.api_key = "test_key"
		provider.api_base_url = "https://api.openai.com/v1"
		provider.default_model = "gpt-4o-mini"
		provider.extra_headers = '{"X-Custom-Header": "value", "X-API-Version": "2024-01"}'

		# Should save successfully
		provider.save()

		# Verify extra headers
		self.assertIn("X-Custom-Header", provider.extra_headers)

	def test_14_inactive_provider(self):
		"""Test inactive provider configuration"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "OpenAI"
		provider.api_key = "test_key"
		provider.api_base_url = "https://api.openai.com/v1"
		provider.default_model = "gpt-4o-mini"
		provider.is_active = 0  # Inactive

		# Should save successfully
		provider.save()

		# Verify inactive status
		self.assertEqual(provider.is_active, 0)

	def test_15_azure_openai_configuration(self):
		"""Test Azure OpenAI configuration (tests real-world use case)"""
		provider = frappe.get_single("AI Provider")

		provider.provider = "Azure OpenAI"
		provider.api_key = "azure_api_key"
		provider.api_base_url = "https://your-resource.openai.azure.com/openai/deployments/your-deployment"
		provider.default_model = "gpt-4"
		provider.is_active = 1

		# Should save successfully
		provider.save()

		# Verify configuration
		self.assertEqual(provider.provider, "Azure OpenAI")
		self.assertIn("azure", provider.api_base_url.lower())
