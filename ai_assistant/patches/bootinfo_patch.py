
# Auto-patch for bootinfo - Compatible with Frappe v15
import frappe


def execute():
    """
    Ensure AI Assistant module is properly registered in the system.
    This patch is compatible with Frappe v15.
    """
    try:
        # Check if AI Assistant module exists
        if not frappe.db.exists("Module Def", "AI Assistant"):
            # Create Module Def for AI Assistant
            module_def = frappe.new_doc("Module Def")
            module_def.module_name = "AI Assistant"
            module_def.app_name = "ai_assistant"
            module_def.insert(ignore_permissions=True)
            frappe.db.commit()
            print("Created Module Def for AI Assistant")

        # Ensure AI Assistant is in installed apps
        installed_apps = frappe.get_installed_apps()
        if "ai_assistant" not in installed_apps:
            print("Warning: ai_assistant not in installed apps list")

    except Exception as e:
        print(f"Patch execution note: {e}")
        # Non-critical error, continue
