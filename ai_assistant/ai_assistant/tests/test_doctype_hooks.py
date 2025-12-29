"""
Test DocType Hooks

Tests document event hooks for AI Assistant
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ai_assistant.doctype_hooks import inject_ai_assistant, validate_ai_permission


class TestDocTypeHooks(unittest.TestCase):
	"""
	Test DocType hook functions

	Test Coverage:
	- inject_ai_assistant() - onload injection
	- validate_ai_permission() - validation hook
	- Permission handling
	- Error handling
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

		# Configure AI Provider
		provider = frappe.get_single("AI Provider")
		provider.provider = "OpenAI"
		provider.api_key = "test_api_key"
		provider.api_base_url = "https://api.openai.com/v1"
		provider.default_model = "gpt-4o-mini"
		provider.is_active = 1
		provider.save()
		frappe.db.commit()

	def setUp(self):
		"""Set up before each test"""
		frappe.db.rollback()
		frappe.set_user("Administrator")

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	def test_01_inject_ai_assistant_active(self):
		"""Test inject_ai_assistant adds flags when provider active"""
		# Create a mock document
		mock_doc = MagicMock()
		mock_doc.set_onload = MagicMock()

		# Ensure user has AI Assistant User role
		admin = frappe.get_doc("User", "Administrator")
		if "AI Assistant User" not in [r.role for r in admin.roles]:
			admin.add_roles("AI Assistant User")
			frappe.db.commit()

		inject_ai_assistant(mock_doc, "onload")

		# Should have set onload flags
		mock_doc.set_onload.assert_called()

	def test_02_inject_ai_assistant_inactive_provider(self):
		"""Test inject_ai_assistant skips when provider inactive"""
		provider = frappe.get_single("AI Provider")
		provider.is_active = 0
		provider.save()
		frappe.db.commit()

		mock_doc = MagicMock()
		mock_doc.set_onload = MagicMock()

		inject_ai_assistant(mock_doc, "onload")

		# Should not set any flags
		mock_doc.set_onload.assert_not_called()

		# Restore
		provider.is_active = 1
		provider.save()
		frappe.db.commit()

	def test_03_inject_ai_assistant_no_permission(self):
		"""Test inject_ai_assistant skips without permission"""
		frappe.set_user("Guest")

		mock_doc = MagicMock()
		mock_doc.set_onload = MagicMock()

		inject_ai_assistant(mock_doc, "onload")

		# Should not set any flags for Guest
		mock_doc.set_onload.assert_not_called()

		frappe.set_user("Administrator")

	def test_04_inject_ai_assistant_no_role(self):
		"""Test inject_ai_assistant skips without AI Assistant User role"""
		# Create a user without AI Assistant User role
		if not frappe.db.exists("User", "test_no_role@example.com"):
			test_user = frappe.get_doc({
				"doctype": "User",
				"email": "test_no_role@example.com",
				"first_name": "Test",
				"enabled": 1
			}).insert(ignore_permissions=True)
			frappe.db.commit()

		frappe.set_user("test_no_role@example.com")

		mock_doc = MagicMock()
		mock_doc.set_onload = MagicMock()

		inject_ai_assistant(mock_doc, "onload")

		# Should not set flags without role
		mock_doc.set_onload.assert_not_called()

		frappe.set_user("Administrator")

	def test_05_inject_ai_assistant_config_data(self):
		"""Test inject_ai_assistant sets correct config data"""
		mock_doc = MagicMock()
		onload_data = {}

		def capture_onload(key, value):
			onload_data[key] = value

		mock_doc.set_onload = capture_onload

		# Ensure user has role
		admin = frappe.get_doc("User", "Administrator")
		if "AI Assistant User" not in [r.role for r in admin.roles]:
			admin.add_roles("AI Assistant User")
			frappe.db.commit()

		inject_ai_assistant(mock_doc, "onload")

		self.assertIn("ai_assistant_enabled", onload_data)
		self.assertTrue(onload_data["ai_assistant_enabled"])
		self.assertIn("ai_assistant_config", onload_data)
		self.assertIn("provider", onload_data["ai_assistant_config"])

	def test_06_validate_ai_permission_no_flag(self):
		"""Test validate_ai_permission does nothing without flag"""
		mock_doc = MagicMock()
		mock_doc._ai_assistant_used = False

		# Should not raise any error
		validate_ai_permission(mock_doc, "validate")

	def test_07_validate_ai_permission_with_flag(self):
		"""Test validate_ai_permission checks permission when flag set"""
		mock_doc = MagicMock()
		mock_doc._ai_assistant_used = True

		# As Administrator with permission, should not raise
		validate_ai_permission(mock_doc, "validate")

	def test_08_validate_ai_permission_no_permission(self):
		"""Test validate_ai_permission fails without permission"""
		frappe.set_user("Guest")

		mock_doc = MagicMock()
		mock_doc._ai_assistant_used = True

		with self.assertRaises(frappe.ValidationError):
			validate_ai_permission(mock_doc, "validate")

		frappe.set_user("Administrator")

	def test_09_inject_ai_assistant_error_handling(self):
		"""Test inject_ai_assistant handles errors gracefully"""
		mock_doc = MagicMock()

		# Simulate error by mocking frappe.get_single to raise
		with patch('ai_assistant.doctype_hooks.frappe.get_single') as mock_get:
			mock_get.side_effect = frappe.DoesNotExistError("AI Provider not found")

			# Should not raise, just skip silently
			inject_ai_assistant(mock_doc, "onload")

	def test_10_inject_ai_assistant_generic_error(self):
		"""Test inject_ai_assistant handles generic errors"""
		mock_doc = MagicMock()

		# Ensure user has permission and role first
		admin = frappe.get_doc("User", "Administrator")
		if "AI Assistant User" not in [r.role for r in admin.roles]:
			admin.add_roles("AI Assistant User")
			frappe.db.commit()

		# Simulate generic error
		with patch('ai_assistant.doctype_hooks.frappe.get_single') as mock_get:
			mock_get.side_effect = Exception("Generic error")

			# Should not raise, just log error
			inject_ai_assistant(mock_doc, "onload")

