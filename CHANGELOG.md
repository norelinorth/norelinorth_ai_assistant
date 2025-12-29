# Changelog - AI Assistant

All notable changes to the AI Assistant app will be documented in this file.

## [2.2.0] - 2025-12-29

### Added
- **Comprehensive Test Suite** - Expanded from 65 to 152 tests
  - `test_api.py` - Tests for session management and chat API (15 tests)
  - `test_ai_provider_resolver.py` - Tests for provider resolution (20 tests)
  - `test_ai_provider_wrapper.py` - Tests for variance analysis integration (10 tests)
  - `test_ai_chat.py` - Tests for chat page functions (12 tests)
  - `test_doctype_hooks.py` - Tests for document event hooks (10 tests)
  - `test_install.py` - Tests for installation procedures (20 tests)

### Changed
- **Test Coverage** - Increased from 29% to 83% (exceeds 80% marketplace requirement)
- **Password Handling in Tests** - Updated to use standard Frappe pattern (direct field assignment)
- **GitHub Repository** - Migrated from winzigkaemme to norelinorth

### Fixed
- Fixed test failures related to Password field handling
- Fixed install.py to not set non-existent DocType fields (temperature, max_tokens)
- Removed references to development tool from documentation

---

## [2.1.1] - 2025-10-06

### Fixed
- **API Key Detection Issue** - Fixed incorrect import pattern in `ai_provider_api.py`
  - Changed from `frappe.utils.password.get_decrypted_password()` to proper import
  - Now uses standard Frappe pattern: `from frappe.utils.password import get_decrypted_password`
  - Matches Frappe core code patterns used in OAuth and authentication systems
  - Resolves issue where API key was set but reported as 'NOT_SET'

### Changed
- **Standards Alignment** - Updated to match production Frappe core patterns
  - `ai_provider_api.py` now uses the same import pattern as `frappe/utils/oauth.py`
  - More reliable password retrieval
  - Better IDE support and type hints

### Documentation
- Added `STANDARDS_VERIFICATION.md` - Detailed verification of Frappe standards compliance
- Documents evidence from Frappe core code (OAuth, Login, BaseDocument)

---

## [2.1.0] - 2024-09-17

### Added
- AI Provider API for multi-app usage
- Simplified API interface without unnecessary class wrappers
- Shared AI Provider configuration for all apps

### Features
- AI chat panel in Sales Orders, Purchase Orders, Invoices
- Context-aware responses using document data
- Session-based conversations
- Permission-based access control

---

## Technical Details for v2.1.1

### Files Modified
- `ai_assistant/ai_provider_api.py`:
  - Line 8: Added `from frappe.utils.password import get_decrypted_password`
  - Line 26: Changed `frappe.utils.password.get_decrypted_password(...)` → `get_decrypted_password(...)`
  - Line 68: Changed `frappe.utils.password.get_decrypted_password(...)` → `get_decrypted_password(...)`

### Why This Change?
The module-level access pattern `frappe.utils.password.get_decrypted_password()` can fail in certain import scenarios. The direct import pattern is:
1. Used in Frappe production code (OAuth, Login systems)
2. More reliable (guarantees module is loaded)
3. Python PEP 8 recommended (explicit imports)
4. Better for type checking and IDE support

### Backward Compatibility
✅ This is a **non-breaking change**
- API interface remains unchanged
- Return values are identical
- No database changes
- No new dependencies

### Testing
To verify the fix works:
```python
import frappe
frappe.connect()

# Test API key detection
config = frappe.call("ai_assistant.ai_provider_api.get_ai_config")
print(config['api_key_status'])  # Should print: 'SET'
```

### References
- See `STANDARDS_VERIFICATION.md` for detailed analysis
- Frappe core examples: `frappe/utils/oauth.py`, `frappe/model/base_document.py`
