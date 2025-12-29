import frappe
from frappe import _


@frappe.whitelist()
def get_recent_sessions():
	"""Get recent AI Assistant sessions for current user - real database data"""
	return frappe.get_all(
		"AI Assistant Session",
		filters={"owner": frappe.session.user},
		fields=["name", "status", "target_doctype", "target_name", "started_on", "last_activity"],
		order_by="modified desc",
		limit=10
	)

@frappe.whitelist()
def get_session_messages(session_name):
	"""Get messages for a session - real database data"""
	session_doc = frappe.get_doc("AI Assistant Session", session_name)
	if not frappe.has_permission(doc=session_doc, ptype="read"):
		frappe.throw(_("Not permitted to read this session"))

	return {
		"session": {
			"name": session_doc.name,
			"status": session_doc.status,
			"target_doctype": session_doc.target_doctype,
			"target_name": session_doc.target_name,
			"started_on": session_doc.started_on
		},
		"messages": session_doc.messages or []
	}

@frappe.whitelist()
def get_available_doctypes():
	"""Get list of DocTypes user can access - real metadata from database"""
	doctypes = frappe.get_all(
		"DocType",
		filters={
			"istable": 0,
			"issingle": 0,
			"module": ["not in", ["Core", "Email", "Custom", "Printing", "Desk"]]
		},
		fields=["name", "module"],
		order_by="name"
	)

	# Filter by user permissions
	allowed = []
	for dt in doctypes:
		if frappe.has_permission(dt.name, "read"):
			allowed.append(dt)

	return allowed
