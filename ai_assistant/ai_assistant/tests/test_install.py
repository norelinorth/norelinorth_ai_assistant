"""
Test AI Assistant Installation Module

Tests installation functions and setup procedures
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ai_assistant.install import (
	REQUIRED_ROLES,
	after_install,
	create_ai_provider_singleton,
	create_default_reports,
	ensure_module_def,
	setup_roles_and_permissions,
	setup_workspace,
)


class TestInstall(unittest.TestCase):
	"""
	Test installation module functions

	Test Coverage:
	- setup_roles_and_permissions() - role creation
	- create_ai_provider_singleton() - singleton creation
	- setup_workspace() - workspace setup
	- create_default_reports() - report creation
	- ensure_module_def() - module definition
	- after_install() - complete installation
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

	def setUp(self):
		"""Set up before each test"""
		frappe.db.rollback()
		frappe.set_user("Administrator")

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	def test_01_required_roles_defined(self):
		"""Test REQUIRED_ROLES constant is defined"""
		self.assertIsInstance(REQUIRED_ROLES, list)
		self.assertIn("AI Assistant User", REQUIRED_ROLES)
		self.assertIn("AI Assistant Admin", REQUIRED_ROLES)

	def test_02_setup_roles_and_permissions_creates_roles(self):
		"""Test setup_roles_and_permissions creates required roles"""
		# Roles should already exist from installation
		for role_name in REQUIRED_ROLES:
			self.assertTrue(frappe.db.exists("Role", role_name))

	def test_03_setup_roles_and_permissions_idempotent(self):
		"""Test setup_roles_and_permissions is idempotent"""
		# Running twice should not raise errors
		setup_roles_and_permissions()
		setup_roles_and_permissions()

		# Roles should still exist
		for role_name in REQUIRED_ROLES:
			self.assertTrue(frappe.db.exists("Role", role_name))

	def test_04_setup_roles_admin_has_roles(self):
		"""Test Administrator has AI Assistant roles"""
		admin = frappe.get_doc("User", "Administrator")
		user_roles = [r.role for r in admin.roles]

		self.assertIn("AI Assistant User", user_roles)
		self.assertIn("AI Assistant Admin", user_roles)

	def test_05_create_ai_provider_singleton(self):
		"""Test AI Provider singleton creation"""
		# Should already exist from installation
		self.assertTrue(frappe.db.exists("AI Provider", "AI Provider"))

	def test_06_create_ai_provider_singleton_idempotent(self):
		"""Test create_ai_provider_singleton is idempotent"""
		# Running twice should not raise errors
		create_ai_provider_singleton()
		create_ai_provider_singleton()

		# Singleton should still exist
		self.assertTrue(frappe.db.exists("AI Provider", "AI Provider"))

	def test_07_ensure_module_def(self):
		"""Test ensure_module_def creates module definition"""
		# Should already exist from installation
		self.assertTrue(frappe.db.exists("Module Def", "AI Assistant"))

	def test_08_ensure_module_def_idempotent(self):
		"""Test ensure_module_def is idempotent"""
		ensure_module_def()
		ensure_module_def()

		self.assertTrue(frappe.db.exists("Module Def", "AI Assistant"))

	def test_09_setup_workspace(self):
		"""Test workspace setup"""
		# Should already exist from installation
		self.assertTrue(frappe.db.exists("Workspace", "AI Assistant"))

	def test_10_setup_workspace_idempotent(self):
		"""Test setup_workspace is idempotent"""
		setup_workspace()
		setup_workspace()

		self.assertTrue(frappe.db.exists("Workspace", "AI Assistant"))

	def test_11_setup_workspace_fields(self):
		"""Test workspace has correct fields"""
		workspace = frappe.get_doc("Workspace", "AI Assistant")

		self.assertEqual(workspace.label, "AI Assistant")
		self.assertEqual(workspace.module, "AI Assistant")
		self.assertIsNotNone(workspace.icon)

	def test_12_setup_workspace_shortcuts(self):
		"""Test workspace has shortcuts"""
		workspace = frappe.get_doc("Workspace", "AI Assistant")

		self.assertGreater(len(workspace.shortcuts), 0)

		# Should have AI Sessions shortcut
		shortcut_labels = [s.label for s in workspace.shortcuts]
		self.assertIn("AI Sessions", shortcut_labels)

	def test_13_create_default_reports(self):
		"""Test default reports creation"""
		# Run report creation
		create_default_reports()

		# Check reports exist
		self.assertTrue(frappe.db.exists("Report", "AI Session Summary"))

	def test_14_create_default_reports_idempotent(self):
		"""Test create_default_reports is idempotent"""
		create_default_reports()
		create_default_reports()

		# Should still exist
		self.assertTrue(frappe.db.exists("Report", "AI Session Summary"))

	def test_15_after_install_complete(self):
		"""Test after_install runs all setup functions"""
		# This is already run during installation
		# Just verify the end state is correct
		self.assertTrue(frappe.db.exists("AI Provider", "AI Provider"))
		self.assertTrue(frappe.db.exists("Workspace", "AI Assistant"))
		self.assertTrue(frappe.db.exists("Module Def", "AI Assistant"))

		for role_name in REQUIRED_ROLES:
			self.assertTrue(frappe.db.exists("Role", role_name))

	def test_16_after_install_idempotent(self):
		"""Test after_install is idempotent"""
		# Running again should not cause errors
		after_install()

		# All components should still exist
		self.assertTrue(frappe.db.exists("AI Provider", "AI Provider"))
		self.assertTrue(frappe.db.exists("Workspace", "AI Assistant"))

	def test_17_ai_provider_default_values(self):
		"""Test AI Provider has sensible defaults"""
		provider = frappe.get_single("AI Provider")

		# Should have is_active default value
		# Note: temperature and max_tokens are not part of the DocType schema
		# They are handled at the API level
		self.assertIsNotNone(provider.is_active)

		# Should have langfuse_host default
		self.assertEqual(provider.langfuse_host, "https://cloud.langfuse.com")

	def test_18_role_has_desk_access(self):
		"""Test AI Assistant roles have desk access"""
		for role_name in REQUIRED_ROLES:
			role = frappe.get_doc("Role", role_name)
			self.assertEqual(role.desk_access, 1)

	def test_19_workspace_module(self):
		"""Test workspace has correct module"""
		workspace = frappe.get_doc("Workspace", "AI Assistant")
		self.assertEqual(workspace.module, "AI Assistant")

	def test_20_reports_are_standard(self):
		"""Test reports are marked as standard"""
		if frappe.db.exists("Report", "AI Session Summary"):
			report = frappe.get_doc("Report", "AI Session Summary")
			self.assertEqual(report.is_standard, "Yes")

