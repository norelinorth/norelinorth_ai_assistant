"""
Test AI Assistant API

Tests session management and chat functionality
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ai_assistant.api import (
	_extract_context,
	chat_once,
	get_provider_config,
	start_session,
	test_context_extraction,
)


class TestAPI(unittest.TestCase):
	"""
	Test AI Assistant API functions

	Test Coverage:
	- start_session() - session creation
	- chat_once() - chat functionality
	- _extract_context() - context extraction
	- get_provider_config() - config retrieval
	- Permission checks
	"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment once"""
		frappe.set_user("Administrator")

		# Ensure AI Provider is configured for tests
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

	def test_01_start_session_basic(self):
		"""Test basic session creation"""
		result = start_session()

		self.assertIsNotNone(result)
		self.assertIn("name", result)
		# Session name is auto-generated hash, just verify it exists
		self.assertIsNotNone(result["name"])

		# Verify session exists
		session = frappe.get_doc("AI Assistant Session", result["name"])
		self.assertEqual(session.status, "Active")
		self.assertIsNone(session.target_doctype)

	def test_02_start_session_with_context(self):
		"""Test session creation with document context"""
		# Use User doctype as context (always exists)
		result = start_session(target_doctype="User", target_name="Administrator")

		self.assertIsNotNone(result)
		session = frappe.get_doc("AI Assistant Session", result["name"])
		self.assertEqual(session.target_doctype, "User")
		self.assertEqual(session.target_name, "Administrator")

	def test_03_start_session_permission_check(self):
		"""Test session creation fails without permission"""
		frappe.set_user("Guest")

		with self.assertRaises(frappe.ValidationError):
			start_session()

		frappe.set_user("Administrator")

	def test_04_start_session_invalid_context(self):
		"""Test session creation fails with invalid context"""
		frappe.set_user("Guest")

		# Guest can't read User doctype
		with self.assertRaises(Exception):
			start_session(target_doctype="User", target_name="Administrator")

		frappe.set_user("Administrator")

	@patch('ai_assistant.api.call_ai')
	def test_05_chat_once_success(self, mock_call_ai):
		"""Test successful chat message"""
		mock_call_ai.return_value = "This is a test response"

		# Create session first
		session_result = start_session()
		session_name = session_result["name"]

		# Send chat message
		result = chat_once(session=session_name, prompt="Hello, how are you?")

		self.assertIsNotNone(result)
		self.assertIn("reply", result)
		self.assertEqual(result["reply"], "This is a test response")

		# Verify messages saved
		session = frappe.get_doc("AI Assistant Session", session_name)
		self.assertEqual(len(session.messages), 2)  # user + assistant
		self.assertEqual(session.messages[0].role, "user")
		self.assertEqual(session.messages[1].role, "assistant")

	def test_06_chat_once_empty_prompt(self):
		"""Test chat fails with empty prompt"""
		session_result = start_session()

		with self.assertRaises(frappe.ValidationError):
			chat_once(session=session_result["name"], prompt="")

	def test_07_chat_once_invalid_session(self):
		"""Test chat fails with invalid session"""
		with self.assertRaises(frappe.ValidationError):
			chat_once(session="INVALID-SESSION", prompt="Hello")

	def test_08_chat_once_permission_check(self):
		"""Test chat fails without permission"""
		session_result = start_session()

		frappe.set_user("Guest")

		with self.assertRaises(Exception):
			chat_once(session=session_result["name"], prompt="Hello")

		frappe.set_user("Administrator")

	@patch('ai_assistant.api.call_ai')
	def test_09_chat_once_with_context(self, mock_call_ai):
		"""Test chat with document context"""
		mock_call_ai.return_value = "Response with context"

		# Create session with context
		session_result = start_session(target_doctype="User", target_name="Administrator")

		result = chat_once(session=session_result["name"], prompt="Tell me about this user")

		self.assertEqual(result["reply"], "Response with context")
		# Verify context was passed to call_ai
		mock_call_ai.assert_called_once()
		call_args = mock_call_ai.call_args
		self.assertIn("context", call_args.kwargs)

	def test_10_extract_context_user(self):
		"""Test context extraction from User doctype"""
		context = _extract_context("User", "Administrator")

		self.assertIn("scalar", context)
		self.assertIn("_doctype", context["scalar"])
		self.assertIn("_name", context["scalar"])
		self.assertEqual(context["scalar"]["_doctype"], "User")
		self.assertEqual(context["scalar"]["_name"], "Administrator")

	def test_11_extract_context_with_children(self):
		"""Test context extraction includes child tables"""
		# User has 'roles' child table
		context = _extract_context("User", "Administrator")

		# Admin should have roles
		self.assertIn("children", context)
		# roles is a child table on User
		if "roles" in context["children"]:
			self.assertIsInstance(context["children"]["roles"], list)

	def test_12_get_provider_config(self):
		"""Test get_provider_config returns config"""
		config = get_provider_config()

		self.assertIsNotNone(config)
		self.assertIn("provider", config)
		self.assertIn("is_active", config)

	def test_13_test_context_extraction_api(self):
		"""Test context extraction API endpoint"""
		result = test_context_extraction("User", "Administrator")

		self.assertIn("scalar", result)
		self.assertIn("_debug_info", result)
		self.assertEqual(result["_debug_info"]["extraction_method"], "dynamic_frappe_meta")

	def test_14_test_context_extraction_permission(self):
		"""Test context extraction requires permission"""
		frappe.set_user("Guest")

		with self.assertRaises(frappe.ValidationError):
			test_context_extraction("User", "Administrator")

		frappe.set_user("Administrator")

	@patch('ai_assistant.api.call_ai')
	def test_15_chat_ai_error_handling(self, mock_call_ai):
		"""Test chat handles AI errors gracefully"""
		mock_call_ai.side_effect = Exception("API Error")

		session_result = start_session()

		with self.assertRaises(frappe.ValidationError) as context:
			chat_once(session=session_result["name"], prompt="Hello")

		self.assertIn("unavailable", str(context.exception).lower())

