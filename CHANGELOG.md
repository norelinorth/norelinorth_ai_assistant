# Changelog

All notable changes to AI Assistant will be documented in this file.

## [2.4.3] - 2026-01-13

### Changed
- Modernized packaging structure using `pyproject.toml` exclusively
- Removed deprecated `setup.py` and `requirements.txt`
- Aligns with Python PEP 518/621 standards and Frappe marketplace requirements
- Updated documentation to explicitly mention Frappe/ERPNext v16 support

---

## [2.4.0] - 2026-01-02

### Added
- Frappe Framework v16 compatibility
- V16_MIGRATION.md documentation for marketplace submission
- Python 3.13 and 3.14 classifiers

### Changed
- DocType sort_field updated from `modified` to `creation` (v16 default)
  - AI Assistant Session
  - AI Provider
  - AI Message

### Verified v16 Compatibility
- No deprecated `frappe.flags.in_test` usage
- No deprecated translation methods
- No custom has_permission hooks requiring updates
- All queries use explicit order_by clauses
- JavaScript follows proper frappe.provide() pattern

---

## [2.3.0] - 2025-12-30

### Changed
- Streamlined package metadata
- Improved documentation structure
- Updated MANIFEST.in for cleaner package builds

---

## [2.2.0] - 2025-12-29

### Added
- Comprehensive test suite with 152 tests
- Test coverage at 83% (exceeds marketplace requirement)
- GitHub Actions CI/CD pipeline

### Fixed
- Module path references for renamed package
- JavaScript API paths for proper integration
- Password handling in tests using standard Frappe patterns

---

## [2.1.1] - 2025-10-06

### Fixed
- API key detection using standard Frappe import pattern
- Aligns with Frappe core patterns (OAuth, authentication systems)

---

## [2.1.0] - 2024-09-17

### Added
- AI Provider API for multi-app usage
- Simplified API interface
- Shared AI Provider configuration

### Features
- AI chat panel in Sales Orders, Purchase Orders, Invoices
- Context-aware responses using document data
- Session-based conversations
- Permission-based access control
- Langfuse observability integration
