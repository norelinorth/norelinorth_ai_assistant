"""
Test AI Chat Page

Tests page functions for AI Chat interface
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ai_assistant.ai_assistant.page.ai_chat.ai_chat import (
	get_available_doctypes,
	get_recent_sessions,
	get_session_messages,
)


class TestAIChat(unittest.TestCase):
	"""
	Test AI Chat page functions

	Test Coverage:
	- get_recent_sessions() - session listing
	- get_session_messages() - message retrieval
	- get_available_doctypes() - doctype listing
	- Permission checks
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

		# Ensure AI Provider is configured
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

	def test_01_get_recent_sessions_empty(self):
		"""Test get_recent_sessions returns empty list when no sessions"""
		# Delete any existing sessions
		frappe.db.delete("AI Assistant Session", {"owner": frappe.session.user})
		frappe.db.commit()

		result = get_recent_sessions()

		self.assertIsInstance(result, list)
		self.assertEqual(len(result), 0)

	def test_02_get_recent_sessions_with_data(self):
		"""Test get_recent_sessions returns sessions"""
		# Create a test session
		session = frappe.get_doc({
			"doctype": "AI Assistant Session",
			"status": "Active"
		}).insert()
		frappe.db.commit()

		result = get_recent_sessions()

		self.assertIsInstance(result, list)
		self.assertGreaterEqual(len(result), 1)

		# Verify fields returned
		session_data = result[0]
		self.assertIn("name", session_data)
		self.assertIn("status", session_data)
		self.assertIn("started_on", session_data)

	def test_03_get_recent_sessions_user_filter(self):
		"""Test get_recent_sessions only returns user's sessions"""
		# Create session as Administrator
		session1 = frappe.get_doc({
			"doctype": "AI Assistant Session",
			"status": "Active"
		}).insert()
		frappe.db.commit()

		# Get sessions - should only see Administrator's sessions
		result = get_recent_sessions()

		for session in result:
			# All sessions should belong to current user
			actual_owner = frappe.db.get_value("AI Assistant Session", session["name"], "owner")
			self.assertEqual(actual_owner, frappe.session.user)

	def test_04_get_recent_sessions_limit(self):
		"""Test get_recent_sessions limits to 10 results"""
		# Create 15 sessions
		for i in range(15):
			frappe.get_doc({
				"doctype": "AI Assistant Session",
				"status": "Active"
			}).insert()
		frappe.db.commit()

		result = get_recent_sessions()

		self.assertLessEqual(len(result), 10)

	def test_05_get_session_messages_success(self):
		"""Test get_session_messages returns session data"""
		# Create session with messages
		session = frappe.get_doc({
			"doctype": "AI Assistant Session",
			"status": "Active"
		}).insert()

		session.append("messages", {"role": "user", "content": "Hello"})
		session.append("messages", {"role": "assistant", "content": "Hi there"})
		session.save()
		frappe.db.commit()

		result = get_session_messages(session.name)

		self.assertIn("session", result)
		self.assertIn("messages", result)
		self.assertEqual(result["session"]["name"], session.name)
		self.assertEqual(len(result["messages"]), 2)

	def test_06_get_session_messages_permission_check(self):
		"""Test get_session_messages checks permission"""
		# Create session as Administrator
		session = frappe.get_doc({
			"doctype": "AI Assistant Session",
			"status": "Active"
		}).insert()
		frappe.db.commit()

		# Try to access as Guest
		frappe.set_user("Guest")

		with self.assertRaises(frappe.ValidationError):
			get_session_messages(session.name)

		frappe.set_user("Administrator")

	def test_07_get_session_messages_not_found(self):
		"""Test get_session_messages with invalid session"""
		with self.assertRaises(frappe.DoesNotExistError):
			get_session_messages("INVALID-SESSION-NAME")

	def test_08_get_available_doctypes(self):
		"""Test get_available_doctypes returns doctype list"""
		result = get_available_doctypes()

		self.assertIsInstance(result, list)
		# Should return some doctypes for Administrator
		self.assertGreater(len(result), 0)

		# Verify structure
		if result:
			self.assertIn("name", result[0])
			self.assertIn("module", result[0])

	def test_09_get_available_doctypes_excludes_system(self):
		"""Test get_available_doctypes excludes system modules"""
		result = get_available_doctypes()

		# Should not include Core doctypes
		core_doctypes = [dt for dt in result if dt.get("module") == "Core"]
		self.assertEqual(len(core_doctypes), 0)

	def test_10_get_available_doctypes_excludes_tables(self):
		"""Test get_available_doctypes excludes child tables"""
		result = get_available_doctypes()

		# None should be child tables (istable=1)
		for dt in result:
			is_table = frappe.db.get_value("DocType", dt["name"], "istable")
			self.assertFalse(is_table)

	def test_11_get_available_doctypes_excludes_singles(self):
		"""Test get_available_doctypes excludes single doctypes"""
		result = get_available_doctypes()

		# None should be single doctypes (issingle=1)
		for dt in result[:20]:  # Check first 20 to save time
			is_single = frappe.db.get_value("DocType", dt["name"], "issingle")
			self.assertFalse(is_single)

	def test_12_get_available_doctypes_permission_filter(self):
		"""Test get_available_doctypes filters by user permission"""
		# As Administrator, should see many doctypes
		admin_result = get_available_doctypes()
		admin_count = len(admin_result)

		# As Guest, should see fewer (or none)
		frappe.set_user("Guest")
		guest_result = get_available_doctypes()
		guest_count = len(guest_result)

		frappe.set_user("Administrator")

		# Guest should see fewer doctypes than Admin
		self.assertLess(guest_count, admin_count)

