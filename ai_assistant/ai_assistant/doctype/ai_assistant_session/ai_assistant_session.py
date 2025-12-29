from frappe.model.document import Document
from frappe.utils import now_datetime


class AIAssistantSession(Document):
    def before_save(self):
        self.last_activity = self.last_activity or now_datetime()
