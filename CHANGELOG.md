# Changelog

All notable changes to AI Assistant will be documented in this file.

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
