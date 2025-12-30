# AI Assistant - Installation Package Creation Guide

**Version:** 2.1.1
**Author:** Noreli North
**Status:** Ready for marketplace submission

---

## Quick Reference

The AI Assistant app is now marketplace-ready with all fixes applied.

---

## Creating the Installation Package

### Method 1: Using setuptools (Standard)

```bash
cd /Users/christian.haeussinger/Desktop/ERPNext-Fresh/frappe-bench/apps/ai_assistant

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Create source distribution
python setup.py sdist

# The package will be in dist/ai_assistant-2.1.1.tar.gz
```

### Method 2: Using build (Modern)

```bash
cd /Users/christian.haeussinger/Desktop/ERPNext-Fresh/frappe-bench/apps/ai_assistant

# Install build tool (if not already installed)
pip install build

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Create distribution
python -m build

# The package will be in dist/ai_assistant-2.1.1.tar.gz
```

### Method 3: Using bench (Frappe-specific)

```bash
cd /Users/christian.haeussinger/Desktop/ERPNext-Fresh/frappe-bench

# Frappe bench can create a release
bench release ai_assistant production --version 2.1.1
```

---

## What Gets Included

Based on `MANIFEST.in`, the package includes:

### Core Files
- setup.py
- pyproject.toml
- requirements.txt
- LICENSE
- MANIFEST.in

### Documentation (User-Facing)
- README.md
- INSTALLATION.md
- CHANGELOG.md
- CONTRIBUTING.md
- PACKAGE_CONTENTS.md
- LANGFUSE_OBSERVABILITY.md
- LANGFUSE_QUICKSTART.md
- LANGFUSE_FILTERING.md
- IMPLEMENTATION_SUMMARY.md

### App Files
- All Python files (`*.py`)
- All JSON files (`*.json`)
- All JavaScript files (`*.js`)
- All HTML files (`*.html`)
- All CSS files (`*.css`)

### Excluded Files
- Shell scripts (`*.sh`)
- Development documentation (in `dev_docs/`)
- Development tools (in `dev_tools/`)
- Python cache (`__pycache__/`, `*.pyc`)
- Internal audit reports

---

## Testing the Package

### 1. Test Installation Locally

```bash
# Create test site
cd /Users/christian.haeussinger/Desktop/ERPNext-Fresh/frappe-bench
bench new-site test-ai.local

# Install from local directory
bench --site test-ai.local install-app norelinorth_ai_assistant

# Run tests
bench --site test-ai.local run-tests --app ai_assistant
```

### 2. Test Installation from Package

```bash
# Install from tarball
bench get-app /path/to/dist/ai_assistant-2.1.1.tar.gz
bench --site test-ai.local install-app norelinorth_ai_assistant

# Verify
bench --site test-ai.local list-apps
```

### 3. Verify Post-Installation

```bash
# Check if workspace appears
# Open ERPNext → AI Assistant workspace

# Check if AI Provider is available
# Open ERPNext → AI Provider

# Check tests pass
bench --site test-ai.local run-tests --app ai_assistant
```

---

## Frappe Marketplace Submission

### Prerequisites

1. **Frappe.io Account** - Sign up at https://frappecloud.com/marketplace
2. **App Repository** - Host code on GitHub/GitLab
3. **Screenshots** - Prepare 3-5 screenshots of the app in action
4. **Icon** - Create 512x512 app icon (PNG)

### Submission Steps

1. **Prepare Package**
   ```bash
   cd apps/ai_assistant
   python setup.py sdist
   ```

2. **Upload to Marketplace**
   - Go to https://frappecloud.com/marketplace/apps
   - Click "Submit New App"
   - Fill in details:
     - App Name: AI Assistant
     - Category: Artificial Intelligence / Productivity
     - Description: Embedded AI Assistant inside ERPNext DocTypes with Langfuse observability
     - Version: 2.1.1
     - Author: Noreli North
     - License: MIT
   - Upload package (dist/ai_assistant-2.1.1.tar.gz)
   - Upload screenshots
   - Upload icon

3. **Documentation Links**
   - GitHub repository URL
   - Documentation URL (link to README.md)
   - Support: GitHub Issues

4. **Submit for Review**
   - Frappe team will review (typically 3-7 days)
   - Address any feedback
   - App goes live after approval

---

## GitHub Release (Optional but Recommended)

### 1. Commit All Changes

```bash
cd /Users/christian.haeussinger/Desktop/ERPNext-Fresh/frappe-bench/apps/ai_assistant

git add .
git commit -m "Release v2.1.1 - Marketplace ready

- Fixed pyproject.toml author metadata
- Updated MANIFEST.in to exclude dev files
- Organized development documentation
- Added CONTRIBUTING.md
- Added comprehensive marketplace documentation
- 100% Frappe/ERPNext standards compliance
- Ready for marketplace submission"
```

### 2. Create Git Tag

```bash
git tag -a v2.1.1 -m "Release v2.1.1 - Marketplace ready

Features:
- AI Provider (Single DocType) - Shared AI configuration
- AI Assistant - Embedded AI chat in ERPNext forms
- Langfuse Observability - Optional LLM tracing
- Multi-App API - Simple API for other apps
- Session Management - Conversation persistence
- Permission Control - Role-based access control

Standards:
- 100% Frappe/ERPNext compliance
- Comprehensive test suite
- Professional documentation
- Security best practices
- MIT License"
```

### 3. Push to GitHub

```bash
git push origin main
git push origin v2.1.1
```

### 4. Create GitHub Release

- Go to your repository on GitHub
- Click "Releases" → "Create a new release"
- Choose tag: v2.1.1
- Release title: "v2.1.1 - Marketplace Ready"
- Description: Copy from CHANGELOG.md
- Attach files: dist/ai_assistant-2.1.1.tar.gz
- Click "Publish release"

---

## Package Distribution URLs

After publishing, users can install via:

### From Frappe Marketplace
```bash
bench get-app ai_assistant
```

### From GitHub
```bash
bench get-app https://github.com/noreli-north/ai_assistant
```

### From PyPI (if published)
```bash
bench get-app ai_assistant --version 2.1.1
```

---

## Post-Release Checklist

- [ ] Package created successfully
- [ ] Local installation tested
- [ ] Tests pass on clean site
- [ ] Git tag created
- [ ] GitHub release published
- [ ] Marketplace submission completed
- [ ] Documentation links verified
- [ ] GitHub Issues enabled
- [ ] CHANGELOG.md updated
- [ ] Version bumped (if needed)

---

## Support & Maintenance

### User Support
- **Issues**: [GitHub Issues](https://github.com/norelinorth/norelinorth_ai_assistant/issues)
- **Marketplace**: Frappe Marketplace

### Updating the App

When releasing updates:

1. Update version in:
   - setup.py
   - pyproject.toml
   - hooks.py
   - CHANGELOG.md

2. Update CHANGELOG.md with changes

3. Create new package and submit to marketplace

4. Create new GitHub release

---

## Package Verification

Before submission, verify:

```bash
# Check package contents
tar -tzf dist/ai_assistant-2.1.1.tar.gz | head -50

# Verify no dev files included
tar -tzf dist/ai_assistant-2.1.1.tar.gz | grep -E "(dev_docs|dev_tools|\.sh$)" || echo "✓ No dev files"

# Verify all required files included
tar -tzf dist/ai_assistant-2.1.1.tar.gz | grep -E "(README|LICENSE|CHANGELOG)" && echo "✓ Required docs included"
```

---

## Troubleshooting

### Issue: Package too large
**Solution:** Check MANIFEST.in excludes, remove unnecessary files

### Issue: Missing files in package
**Solution:** Update MANIFEST.in to include them explicitly

### Issue: Import errors after installation
**Solution:** Check requirements.txt has all dependencies

### Issue: Tests fail
**Solution:** Ensure test fixtures are included in package

---

## Marketplace Categories

Suggested categories for AI Assistant:

1. **Primary:** Artificial Intelligence
2. **Secondary:** Productivity
3. **Tags:** AI, OpenAI, Langfuse, Chat, Assistant, Automation

---

## Screenshots for Marketplace

Recommended screenshots:

1. **AI Provider Configuration** - Show the AI Provider settings page
2. **AI Assistant in Sales Order** - Chat panel in action
3. **AI Chat Page** - Standalone AI chat page
4. **Langfuse Dashboard** - (Optional) Observability integration
5. **Workspace** - AI Assistant workspace overview

---

**The AI Assistant app is ready for marketplace submission!**

For questions or issues: [GitHub Issues](https://github.com/norelinorth/norelinorth_ai_assistant/issues)

---

*Guide created: 2025-10-26*
*App version: 2.1.1*
*Status: Marketplace Ready ✅*
