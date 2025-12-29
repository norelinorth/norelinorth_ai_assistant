# AI Assistant Installation Guide
## 100% Aligned with Frappe/ERPNext v15

## Quick Installation

```bash
cd frappe-bench
./apps/ai_assistant/install_and_validate.sh working.local.2
```

## Manual Installation Steps

### 1. Install the App
```bash
cd frappe-bench
bench --site working.local.2 install-app ai_assistant
bench --site working.local.2 migrate
```

### 2. Clear Cache and Build Assets
```bash
bench clear-cache
bench --site working.local.2 build --app ai_assistant
```

### 3. Configure AI Provider
1. Navigate to: http://127.0.0.1:8000/app/ai-provider
2. Enter your OpenAI API Key
3. Set provider to "OpenAI"
4. Set default model to "gpt-3.5-turbo"
5. Save the configuration

## Access URLs

- **AI Assistant Workspace**: http://127.0.0.1:8000/app/ai-assistant
- **AI Sessions List**: http://127.0.0.1:8000/app/ai-assistant-session
- **Session Report**: http://127.0.0.1:8000/app/ai-assistant-session/view/report
- **AI Provider Config**: http://127.0.0.1:8000/app/ai-provider

## Integrated DocTypes

AI Assistant is automatically embedded in:
- Sales Order
- Purchase Order
- Sales Invoice
- Purchase Invoice
- Journal Entry

The AI Assistant panel appears automatically in the sidebar when you open these documents.

## Bench Management

### Using Bench Manager (Recommended)
```bash
# Check status
./apps/ai_assistant/bench_manager.sh status

# Start bench
./apps/ai_assistant/bench_manager.sh start

# Stop bench
./apps/ai_assistant/bench_manager.sh stop

# View logs
./apps/ai_assistant/bench_manager.sh logs
```

### Manual Bench Commands
```bash
# Start in foreground
bench start

# Start in background with nohup
nohup bench start > bench.log 2>&1 &

# Stop bench
bench stop
```

## Testing

### Run Complete Test Suite
```bash
cd apps/ai_assistant/ai_assistant/tests
./final_ai_assistant_test.sh
```

### Test UI Integration
```bash
./test_ai_assistant_ui.sh
```

### Diagnose Issues
```bash
./diagnose_ai_assistant.sh
```

## File Structure

```
ai_assistant/
├── ai_assistant/
│   ├── __init__.py
│   ├── hooks.py                     # DocType integration hooks
│   ├── install.py                   # Installation module
│   ├── api.py                       # Whitelisted API methods
│   ├── ai_provider_api.py          # AI provider integration
│   ├── public/
│   │   └── js/
│   │       └── ai_assistant_integration.js  # UI integration
│   ├── ai_assistant/
│   │   └── doctype/
│   │       ├── ai_provider/        # AI Provider singleton
│   │       ├── ai_assistant_session/  # Session management
│   │       └── ai_message/         # Message child table
│   └── tests/                      # Test scripts
│       ├── final_ai_assistant_test.sh
│       ├── test_ai_assistant_ui.sh
│       └── diagnose_ai_assistant.sh
├── install_and_validate.sh         # Master installation script
└── INSTALLATION.md                 # This file
```

## Features

### UI Components (Frappe-Aligned)
- ✅ Embedded AI panel in sidebar (no toolbar button needed)
- ✅ Chat conversation area
- ✅ Message input with Enter key support
- ✅ Send button
- ✅ Suggestions button with predefined prompts
- ✅ Clear conversation button
- ✅ Status indicators
- ✅ Auto-appears in supported DocTypes

### Workspace (Best Practices)
- ✅ DocType shortcut for AI Sessions list
- ✅ Quick access to AI Provider settings
- ✅ No "New Session" (sessions are auto-created when using AI)
- ✅ No individual report shortcuts (following Frappe standards)

### Technical Implementation
- ✅ jQuery.Deferred for promise compatibility
- ✅ Standard function syntax (no arrow functions)
- ✅ Frappe alert and msgprint patterns
- ✅ XSS sanitization
- ✅ Permission checks
- ✅ Session management
- ✅ Bench manager script for reliable server management

## Troubleshooting

### JavaScript Errors
If you see `.finally is not a function`:
- Clear browser cache (Ctrl+Shift+R)
- Run `bench build --app ai_assistant --force`

### AI Provider Not Configured
1. Go to http://127.0.0.1:8000/app/ai-provider
2. Enter a valid OpenAI API key
3. Save the configuration

### DocType Integration Not Working
1. Clear cache: `bench clear-cache`
2. Rebuild: `bench build --app ai_assistant`
3. Restart: `bench restart`

### Database Issues
```bash
bench --site working.local.2 migrate --skip-failing
```

## Requirements

- Frappe Framework v15
- ERPNext v15 (optional)
- Python 3.10+
- OpenAI API key (or compatible provider)

## Support

For issues or questions:
1. Check the test output: `./diagnose_ai_assistant.sh`
2. Review logs: `bench --site working.local.2 console`
3. Check browser console for JavaScript errors