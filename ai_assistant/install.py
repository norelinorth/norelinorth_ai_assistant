"""
AI Assistant Installation Module
Ensures complete setup with all tables, configurations, and workspace
100% Aligned with Frappe/ERPNext v15
"""

from __future__ import annotations

import frappe

REQUIRED_ROLES = ["AI Assistant User", "AI Assistant Admin"]

def after_install():
    """Called after app installation - Complete setup"""
    print("Setting up AI Assistant...")

    # Step 1: Setup roles
    setup_roles_and_permissions()

    # Step 2: Create AI Provider singleton
    create_ai_provider_singleton()

    # Step 3: Setup workspace with reports
    setup_workspace()

    # Step 4: Create default reports
    create_default_reports()

    # Step 5: Ensure Module Def exists
    ensure_module_def()

    # Clear cache and commit
    frappe.clear_cache()
    frappe.db.commit()
    print("✅ AI Assistant setup completed successfully!")

def setup_roles_and_permissions():
    """Setup roles and permissions for AI Assistant"""
    for role_name in REQUIRED_ROLES:
        if not frappe.db.exists("Role", role_name):
            print(f"Creating role: {role_name}")
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.insert(ignore_permissions=True)
            print(f"✅ Role {role_name} created")

    # Assign AI Assistant User role to Administrator
    admin = frappe.get_doc("User", "Administrator")
    if "AI Assistant User" not in [r.role for r in admin.roles]:
        admin.add_roles("AI Assistant User", "AI Assistant Admin")
        print("✅ Administrator granted AI Assistant roles")

    frappe.db.commit()

def create_ai_provider_singleton():
    """Create AI Provider singleton document"""
    try:
        # Check if singleton exists
        if not frappe.db.exists("AI Provider", "AI Provider"):
            print("Creating AI Provider configuration...")
            ai_provider = frappe.new_doc("AI Provider")
            # Set provider to OpenAI as default option but leave configuration empty
            ai_provider.provider = "OpenAI"
            ai_provider.is_active = 0  # Disabled by default until configured
            # Don't set defaults - let user configure these
            # ai_provider.default_model = ""  # User will configure
            # ai_provider.api_key = ""  # User must provide
            ai_provider.flags.ignore_permissions = True
            ai_provider.flags.ignore_mandatory = True
            ai_provider.insert()
            frappe.db.commit()
            print("✅ AI Provider singleton created (requires configuration)")
    except Exception as e:
        print(f"Note: AI Provider setup - {e}")

def ensure_module_def():
    """Ensure Module Def exists for AI Assistant"""
    if not frappe.db.exists("Module Def", "AI Assistant"):
        module_def = frappe.new_doc("Module Def")
        module_def.module_name = "AI Assistant"
        module_def.app_name = "ai_assistant"
        module_def.insert(ignore_permissions=True)
        print("✅ Module Def created for AI Assistant")

def setup_workspace():
    """Setup AI Assistant workspace following Frappe best practices"""
    workspace_name = "AI Assistant"

    shortcuts_def = [
        {
            "label": "AI Sessions",
            "link_to": "AI Assistant Session",
            "type": "DocType",
            "color": "blue",
            "doc_view": "List"
        },
        {
            "label": "AI Provider Settings",
            "link_to": "AI Provider",
            "type": "DocType",
            "color": "green"
        }
    ]

    try:
        if frappe.db.exists("Workspace", workspace_name):
            workspace = frappe.get_doc("Workspace", workspace_name)
        else:
            workspace = frappe.new_doc("Workspace")
            workspace.name = workspace_name

        # Set basic fields
        workspace.label = "AI Assistant"
        workspace.module = "AI Assistant"
        workspace.icon = "support"
        workspace.indicator_color = "blue"
        workspace.is_standard = 1
        workspace.extends_another_page = 0
        workspace.is_default = 0

        # Clear and rebuild shortcuts (child table)
        workspace.shortcuts = []
        for shortcut in shortcuts_def:
            workspace.append("shortcuts", shortcut)

        if workspace.is_new():
            workspace.insert(ignore_permissions=True)
            print(f"✅ Workspace '{workspace_name}' created")
        else:
            workspace.save(ignore_permissions=True)
            print(f"✅ Workspace '{workspace_name}' updated")

        frappe.db.commit()
    except Exception as e:
        print(f"Workspace setup note: {e}")

def create_default_reports():
    """Create default reports for AI Assistant following Frappe standards"""
    reports = [
        {
            "name": "AI Session Summary",
            "ref_doctype": "AI Assistant Session",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "AI Assistant",
            "add_total_row": 0,
            "columns": [
                {"fieldname": "name", "label": "Session ID", "fieldtype": "Link", "options": "AI Assistant Session", "width": 200},
                {"fieldname": "owner", "label": "User", "fieldtype": "Link", "options": "User", "width": 150},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "width": 100},
                {"fieldname": "target_doctype", "label": "DocType", "fieldtype": "Data", "width": 150},
                {"fieldname": "started_on", "label": "Started", "fieldtype": "Datetime", "width": 180},
                {"fieldname": "last_activity", "label": "Last Activity", "fieldtype": "Datetime", "width": 180}
            ],
            "filters": [
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "\nActive\nClosed"},
                {"fieldname": "owner", "label": "User", "fieldtype": "Link", "options": "User"}
            ]
        },
        {
            "name": "AI Usage Analytics",
            "ref_doctype": "AI Assistant Session",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "AI Assistant",
            "add_total_row": 1,
            "columns": [
                {"fieldname": "owner", "label": "User", "fieldtype": "Link", "options": "User", "width": 150},
                {"fieldname": "count", "label": "Total Sessions", "fieldtype": "Int", "width": 120, "aggregate_function": "count"},
                {"fieldname": "target_doctype", "label": "Most Used DocType", "fieldtype": "Data", "width": 150}
            ]
        }
    ]

    for report_def in reports:
        try:
            report_name = report_def["name"]
            if not frappe.db.exists("Report", report_name):
                report = frappe.new_doc("Report")
                # report_name is the required field (not name)
                report.report_name = report_name
                report.ref_doctype = report_def["ref_doctype"]
                report.report_type = report_def["report_type"]
                report.is_standard = report_def.get("is_standard", "No")
                report.module = report_def["module"]
                report.insert(ignore_permissions=True)
                print(f"✅ Report '{report_name}' created")
        except Exception as e:
            print(f"Report note: {e}")

    frappe.db.commit()
