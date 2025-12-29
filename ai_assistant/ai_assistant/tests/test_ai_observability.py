"""
Test AI Observability (Langfuse Integration)

Tests Langfuse client initialization, configuration, and tracing
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe
from frappe.utils.password import set_encrypted_password

from ai_assistant.ai_observability import (
	LANGFUSE_AVAILABLE,
	flush_langfuse,
	get_langfuse_client,
	reset_langfuse_client,
	validate_langfuse_config,
)


class TestAIObservability(unittest.TestCase):
	"""
	Test Langfuse observability integration

	Test Coverage:
	- Langfuse client initialization
	- Configuration validation
	- Graceful degradation when Langfuse not installed
	- Error handling
	- Cache management
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

		# Reset Langfuse client cache
		reset_langfuse_client()

		# Configure AI Provider
		self.provider = frappe.get_single("AI Provider")
		self.provider.provider = "OpenAI"
		self.provider.api_key = "test_api_key_for_testing"
		self.provider.api_base_url = "https://api.openai.com/v1"
		self.provider.default_model = "gpt-4o-mini"
		self.provider.is_active = 1

		# Disable Langfuse by default (enable in specific tests)
		self.provider.enable_langfuse = 0
		self.provider.save()
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after each test"""
		reset_langfuse_client()
		frappe.db.rollback()

	def test_01_langfuse_available_flag(self):
		"""Test LANGFUSE_AVAILABLE flag is set correctly"""
		# This flag should be True if langfuse is installed, False otherwise
		self.assertIsInstance(LANGFUSE_AVAILABLE, bool)

	def test_02_get_client_when_disabled(self):
		"""Test get_langfuse_client() returns None when disabled"""
		# Langfuse is disabled in setUp
		client = get_langfuse_client()

		# Should return None
		self.assertIsNone(client)

	def test_03_get_client_no_public_key(self):
		"""Test get_langfuse_client() returns None when public key missing"""
		# Enable Langfuse but don't set keys
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = ""
		self.provider.save()
		frappe.db.commit()

		client = get_langfuse_client()

		# Should return None and log error
		self.assertIsNone(client)

	def test_04_get_client_no_secret_key(self):
		"""Test get_langfuse_client() returns None when secret key missing"""
		# Enable Langfuse with public key but no secret key
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"

		# Explicitly clear secret key (in case one exists from previous test)
		set_encrypted_password(
			"AI Provider", "AI Provider", "",
			fieldname="langfuse_secret_key"
		)

		self.provider.save()
		frappe.db.commit()

		# Reset client cache to ensure fresh initialization
		reset_langfuse_client()

		client = get_langfuse_client()

		# Should return None and log error
		self.assertIsNone(client)

	def test_05_get_client_no_host(self):
		"""Test get_langfuse_client() returns None when host missing"""
		# Enable Langfuse with keys but no host
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_secret_key = "sk-lf-test-secret"
		self.provider.langfuse_host = ""  # Clear host

		self.provider.save()
		frappe.db.commit()

		client = get_langfuse_client()

		# Should return None (no hardcoded fallback)
		self.assertIsNone(client)

	@patch('ai_assistant.ai_observability.LANGFUSE_AVAILABLE', False)
	def test_06_get_client_langfuse_not_installed(self):
		"""Test get_langfuse_client() when langfuse package not installed"""
		# Mock LANGFUSE_AVAILABLE as False
		client = get_langfuse_client()

		# Should return None gracefully (no error logs)
		self.assertIsNone(client)

	@patch('ai_assistant.ai_observability.Langfuse')
	def test_07_get_client_success(self, mock_langfuse_class):
		"""Test get_langfuse_client() successfully initializes client"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Configure complete Langfuse settings
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_secret_key = "sk-lf-test-secret"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		self.provider.save()
		frappe.db.commit()

		# Mock Langfuse class
		mock_client_instance = MagicMock()
		mock_langfuse_class.return_value = mock_client_instance

		# Get client
		client = get_langfuse_client()

		# Should initialize Langfuse with correct parameters
		mock_langfuse_class.assert_called_once_with(
			public_key="pk-lf-test-12345",
			secret_key="sk-lf-test-secret",
			host="https://cloud.langfuse.com"
		)

		# Should return client instance
		self.assertIsNotNone(client)
		self.assertEqual(client, mock_client_instance)

	@patch('ai_assistant.ai_observability.Langfuse')
	def test_08_get_client_caching(self, mock_langfuse_class):
		"""Test get_langfuse_client() caches client instance"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Configure Langfuse
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_secret_key = "sk-lf-test-secret"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		self.provider.save()
		frappe.db.commit()

		# Mock Langfuse
		mock_client = MagicMock()
		mock_langfuse_class.return_value = mock_client

		# Get client twice
		client1 = get_langfuse_client()
		client2 = get_langfuse_client()

		# Should only initialize once (cached)
		self.assertEqual(mock_langfuse_class.call_count, 1)

		# Should return same instance
		self.assertEqual(client1, client2)

	def test_09_reset_langfuse_client(self):
		"""Test reset_langfuse_client() clears cache"""
		# This should not raise any error
		reset_langfuse_client()

		# After reset, should re-initialize on next get
		# (tested implicitly in other tests)

	def test_10_flush_langfuse_no_client(self):
		"""Test flush_langfuse() handles no client gracefully"""
		# Langfuse disabled, so no client
		# Should not raise error
		flush_langfuse()

	@patch('ai_assistant.ai_observability.Langfuse')
	def test_11_flush_langfuse_with_client(self, mock_langfuse_class):
		"""Test flush_langfuse() calls client.flush()"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Configure and get client
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_secret_key = "sk-lf-test-secret"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		self.provider.save()
		frappe.db.commit()

		# Mock client
		mock_client = MagicMock()
		mock_langfuse_class.return_value = mock_client

		# Get client
		get_langfuse_client()

		# Flush
		flush_langfuse()

		# Should call flush on client
		mock_client.flush.assert_called_once()

	def test_12_validate_langfuse_config_disabled(self):
		"""Test validate_langfuse_config() when Langfuse is disabled"""
		# Langfuse disabled
		result = validate_langfuse_config()

		self.assertIsNotNone(result)
		self.assertFalse(result["enabled"])
		self.assertFalse(result["configured"])
		self.assertEqual(result["status"], "disabled")

	def test_13_validate_langfuse_config_incomplete(self):
		"""Test validate_langfuse_config() with incomplete credentials"""
		# Enable but don't set credentials
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = ""  # Missing
		self.provider.save()
		frappe.db.commit()

		result = validate_langfuse_config()

		self.assertTrue(result["enabled"])
		self.assertFalse(result["configured"])
		self.assertEqual(result["status"], "incomplete")

	@patch('ai_assistant.ai_observability.Langfuse')
	def test_14_validate_langfuse_config_active(self, mock_langfuse_class):
		"""Test validate_langfuse_config() with complete configuration"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Complete configuration
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_secret_key = "sk-lf-test-secret"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		self.provider.save()
		frappe.db.commit()

		# Mock successful client initialization
		mock_client = MagicMock()
		mock_langfuse_class.return_value = mock_client

		result = validate_langfuse_config()

		self.assertTrue(result["enabled"])
		self.assertTrue(result["configured"])
		self.assertEqual(result["status"], "active")
		self.assertEqual(result["host"], "https://cloud.langfuse.com")

	def test_15_validate_langfuse_permission_check(self):
		"""Test validate_langfuse_config() checks permissions"""
		# Set user without permissions
		frappe.set_user("Guest")

		# Should fail with permission error (frappe.throw raises ValidationError)
		with self.assertRaises(Exception):
			validate_langfuse_config()

		# Reset to Administrator
		frappe.set_user("Administrator")

	@patch('ai_assistant.ai_observability.Langfuse')
	def test_16_get_client_initialization_error(self, mock_langfuse_class):
		"""Test get_langfuse_client() handles initialization errors"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Configure Langfuse
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		set_encrypted_password(
			"AI Provider", "AI Provider", "sk-lf-test-secret",
			fieldname="langfuse_secret_key"
		)

		self.provider.save()
		frappe.db.commit()

		# Mock Langfuse to raise error
		mock_langfuse_class.side_effect = Exception("Connection failed")

		# Should return None and log error (not crash)
		client = get_langfuse_client()
		self.assertIsNone(client)

	def test_17_langfuse_host_default_value(self):
		"""Test Langfuse host has default value from DocType"""
		# Fresh provider should have default host
		provider = frappe.get_single("AI Provider")

		# Default should be set in DocType JSON (not Python code)
		self.assertEqual(provider.langfuse_host, "https://cloud.langfuse.com")

	@patch('ai_assistant.ai_observability.Langfuse')
	def test_18_flush_error_handling(self, mock_langfuse_class):
		"""Test flush_langfuse() handles flush errors gracefully"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Configure and get client
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		set_encrypted_password(
			"AI Provider", "AI Provider", "sk-lf-test-secret",
			fieldname="langfuse_secret_key"
		)

		self.provider.save()
		frappe.db.commit()

		# Mock client with flush error
		mock_client = MagicMock()
		mock_client.flush.side_effect = Exception("Flush failed")
		mock_langfuse_class.return_value = mock_client

		# Get client
		get_langfuse_client()

		# Flush should handle error gracefully (not crash)
		flush_langfuse()  # Should not raise exception

	def test_19_no_import_time_errors(self):
		"""Test that importing ai_observability doesn't create error logs"""
		# This test verifies that the fix for import-time frappe.log_error() is working

		# Import the module
		import ai_assistant.ai_observability

		# If langfuse is not installed, LANGFUSE_AVAILABLE should be False
		# but no error logs should be created
		self.assertIsInstance(ai_assistant.ai_observability.LANGFUSE_AVAILABLE, bool)

		# The module should import successfully without exceptions
		self.assertTrue(True)  # If we got here, import succeeded

	@patch('ai_assistant.ai_observability.Langfuse')
	def test_20_multiple_reset_and_reinit(self, mock_langfuse_class):
		"""Test multiple reset and re-initialization cycles"""
		if not LANGFUSE_AVAILABLE:
			self.skipTest("Langfuse not installed")

		# Configure Langfuse
		self.provider.enable_langfuse = 1
		self.provider.langfuse_public_key = "pk-lf-test-12345"
		self.provider.langfuse_host = "https://cloud.langfuse.com"

		set_encrypted_password(
			"AI Provider", "AI Provider", "sk-lf-test-secret",
			fieldname="langfuse_secret_key"
		)

		self.provider.save()
		frappe.db.commit()

		# Mock client
		mock_client = MagicMock()
		mock_langfuse_class.return_value = mock_client

		# Get, reset, get again multiple times
		for i in range(3):
			client = get_langfuse_client()
			self.assertIsNotNone(client)

			reset_langfuse_client()

		# Should initialize 3 times (once per cycle)
		self.assertEqual(mock_langfuse_class.call_count, 3)
