# AI Assistant — Embedded, DB-aware, Frappe/ERPNext-aligned (v2)

**Key points**
- Embedded panel **inside** ERPNext forms (no separate page).
- Real **database context**: we dynamically read DocType meta + document data (no hardcoded fields).
- **OpenAI-only**, *must be configured* in **AI Provider** (no demo fallbacks).
- Permissions enforced: user must have read access to the target document and write permission on AI Assistant Session.
- Audit-friendly DocTypes: AI Provider (Single), AI Assistant Session (Parent), AI Message (Child).

## Install
```bash
cd /path/to/frappe-bench
bench get-app /ABSOLUTE/PATH/TO/THIS/FOLDER
bench --site mysite.local install-app ai_assistant
bench --site mysite.local migrate
bench build --apps ai_assistant
bench clear-cache
bench start
```

## Configure
Desk → **AI Provider** (Single)
- Provider: **OpenAI**
- API Key (Password): your key
- Default Model: e.g. `gpt-4o-mini`
- (Optional) API Base URL: leave blank for api.openai.com

Grant your user **AI Assistant User** role.

## Use
Open an existing **Journal Entry / Purchase Order / Sales Order / Sales Invoice / Purchase Invoice**.  
The **AI Assistant** panel appears in the form dashboard. Type → **Send**.  
Context from the **live document** (scalars + child rows) is sent to OpenAI in a structured JSON block.

## Troubleshooting
- Panel missing → user role or unsaved doc. Then `bench migrate && bench build --apps ai_assistant && bench clear-cache`.
- "Not permitted" → ensure you have read access on the target doc and have **AI Assistant User** role.
- Provider errors → configure **AI Provider** correctly. Check **Error Log** for stack traces.