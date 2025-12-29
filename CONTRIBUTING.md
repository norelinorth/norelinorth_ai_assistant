# Contributing to AI Assistant

Thank you for your interest in contributing to AI Assistant! This document provides guidelines for contributing to this project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. **Check existing issues** - Search the issue tracker to see if it's already reported
2. **Create a new issue** - Include:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - ERPNext/Frappe version
   - Any error messages or logs

### Submitting Pull Requests

1. **Fork the repository** and create a new branch
2. **Follow Frappe/ERPNext standards** - See section below
3. **Write tests** for new features
4. **Update documentation** if needed
5. **Submit PR** with clear description of changes

### Development Setup

```bash
# Get the app
cd frappe-bench
bench get-app ai_assistant

# Install on a site
bench --site yoursite.local install-app ai_assistant

# Run tests
bench --site yoursite.local run-tests --app ai_assistant
```

## Standards and Guidelines

### Code Standards

This app follows **100% Frappe/ERPNext standards compliance**. Please review:

1. **No custom fields** on core DocTypes
2. **No hardcoded values** - All configuration from database
3. **Permission checks** on all whitelisted methods
4. **Translatable strings** - Use `_()` for all user-facing text
5. **SQL safety** - Use Frappe ORM, parameterized queries only
6. **Error logging** - Use `frappe.log_error()` pattern
7. **Type conversion** - Use `flt()`, `cint()`, `cstr()` properly

### Code Style

- **Indentation**: Tabs (Frappe standard)
- **Naming**: snake_case for functions, PascalCase for classes
- **Docstrings**: Comprehensive docstrings for all public functions
- **Comments**: Explain "why", not "what"
- **Line length**: Maximum 99 characters

### Testing Requirements

All contributions must include tests:

- **Unit tests** for individual functions
- **Integration tests** for workflows
- **Minimum 80% coverage** (target 100%)
- Tests must pass: `bench --site site-name run-tests --app ai_assistant`

### Documentation

Update documentation when:

- Adding new features
- Changing API behavior
- Modifying configuration options
- Fixing important bugs

**Required documentation:**
- Code docstrings
- README.md updates
- CHANGELOG.md entry

## Frappe/ERPNext Patterns

### Example: Whitelisted Method with Permission Check

```python
@frappe.whitelist()
def my_function(param1, param2):
	"""
	Brief description

	Args:
		param1 (str): Description
		param2 (dict): Description

	Returns:
		dict: Description of return value
	"""
	# Permission check
	if not frappe.has_permission("DocType Name", "read"):
		frappe.throw(_("Insufficient permissions"))

	# Validate parameters
	if not param1:
		frappe.throw(_("Parameter is required"))

	# Business logic
	result = do_something()

	return result
```

### Example: Error Handling

```python
try:
	# Business logic
	doc.insert()
	frappe.db.commit()
except Exception as e:
	# Log for admin
	frappe.log_error(
		message=f"Detailed error: {str(e)}\n{frappe.get_traceback()}",
		title="Operation Failed"
	)
	# User-friendly message
	frappe.throw(_("An error occurred. Please contact administrator."))
```

## Review Process

1. **Automated checks** - Code must pass any CI/CD checks
2. **Standards review** - Verify Frappe/ERPNext compliance
3. **Testing** - All tests must pass
4. **Documentation** - Required docs must be updated
5. **Maintainer review** - Final review by project maintainers

## Questions?

- **Documentation**: See README.md and INSTALLATION.md
- **Standards**: Review Frappe Framework documentation
- **Issues**: Open a GitHub issue
- **Contact**: honeyspotdaily@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to AI Assistant!** 🚀
