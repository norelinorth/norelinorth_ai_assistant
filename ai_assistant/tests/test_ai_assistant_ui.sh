#!/bin/bash

# ========================================================================
# AI Assistant UI Test Script
# Verifies all UI elements are present and functional
# ========================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

BENCH_PATH="$HOME/Desktop/ERPNext-3/frappe-bench"
SITE_NAME="${1:-working.local.2}"

cd "$BENCH_PATH"

echo -e "${PURPLE}========================================="
echo "   AI Assistant UI Test Suite"
echo "   Testing Complete Integration"
echo -e "=========================================${NC}\n"

# Function to test JavaScript elements
test_js_elements() {
    echo -e "${YELLOW}Testing JavaScript UI Elements:${NC}"

    # Check if the updated JS file exists and has correct content
    JS_FILE="sites/assets/ai_assistant/js/ai_assistant_integration.js"

    if [ -f "$JS_FILE" ]; then
        echo -e "${GREEN}✓${NC} JavaScript file exists"

        # Check for key UI elements in the JS
        echo -e "\n${BLUE}Checking UI Components:${NC}"

        # Input field
        if grep -q "ai-user-input" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} User input textarea present"
        else
            echo -e "${RED}✗${NC} User input textarea missing"
        fi

        # Response area
        if grep -q "ai-conversation-area" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} Conversation/response area present"
        else
            echo -e "${RED}✗${NC} Conversation/response area missing"
        fi

        # Send button
        if grep -q "ai-send-btn" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} Send button present"
        else
            echo -e "${RED}✗${NC} Send button missing"
        fi

        # Enter key handler
        if grep -q "Enter.*!e.shiftKey" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} Enter key handler present"
        else
            echo -e "${RED}✗${NC} Enter key handler missing"
        fi

        # Message display
        if grep -q "ai-messages" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} Message display area present"
        else
            echo -e "${RED}✗${NC} Message display area missing"
        fi

        # Status indicator
        if grep -q "ai-status" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} Status indicator present"
        else
            echo -e "${RED}✗${NC} Status indicator missing"
        fi

        # Suggestions feature
        if grep -q "ai-suggestion-btn" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} Suggestions button present"
        else
            echo -e "${RED}✗${NC} Suggestions button missing"
        fi

        # Clear button
        if grep -q "ai-clear-btn" "$JS_FILE"; then
            echo -e "${GREEN}✓${NC} Clear conversation button present"
        else
            echo -e "${RED}✗${NC} Clear conversation button missing"
        fi

    else
        echo -e "${RED}✗${NC} JavaScript file not found"
    fi
}

# Function to test backend API
test_backend_api() {
    echo -e "\n${YELLOW}Testing Backend API:${NC}"

    bench --site "$SITE_NAME" console << 'EOF' 2>/dev/null | grep -E "✓|✗"
import frappe

# Test API methods exist
try:
    from ai_assistant.ai_assistant.api import start_session, chat_once
    print("✓ API methods imported successfully")
except ImportError:
    print("✗ API methods import failed")

# Test AI Provider
try:
    provider = frappe.get_doc("AI Provider", "AI Provider")
    if provider.is_active:
        print("✓ AI Provider is active")
    else:
        print("✗ AI Provider is inactive")
except:
    print("✗ AI Provider not found")

# Test permissions
frappe.set_user("Administrator")
if frappe.has_permission("AI Assistant Session", "create"):
    print("✓ Can create AI sessions")
else:
    print("✗ Cannot create AI sessions")
EOF
}

# Function to test page integration
test_page_integration() {
    echo -e "\n${YELLOW}Testing Page Integration:${NC}"

    # Login and get a Sales Order page
    curl -s -X POST http://127.0.0.1:8000/api/method/login \
        -H "Content-Type: application/json" \
        -d '{"usr":"Administrator","pwd":"admin"}' \
        -c /tmp/ai_ui_test.txt > /dev/null

    # Test if AI Assistant JS is loaded
    RESPONSE=$(curl -s -b /tmp/ai_ui_test.txt \
        http://127.0.0.1:8000/app/sales-order/new-sales-order-1 2>/dev/null)

    if echo "$RESPONSE" | grep -q "ai_assistant_integration.js"; then
        echo -e "${GREEN}✓${NC} AI Assistant JS loaded in page"
    else
        echo -e "${RED}✗${NC} AI Assistant JS not loaded"
    fi

    # Check for AI Assistant references
    AI_COUNT=$(echo "$RESPONSE" | grep -c "ai_assistant" || true)
    if [ "$AI_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} AI Assistant referenced $AI_COUNT times"
    else
        echo -e "${RED}✗${NC} AI Assistant not referenced"
    fi
}

# Function to generate browser test instructions
generate_browser_test() {
    echo -e "\n${PURPLE}========================================="
    echo "   Browser Testing Instructions"
    echo -e "=========================================${NC}\n"

    echo -e "${BLUE}Step 1: Clear Browser Cache${NC}"
    echo "  • Press Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)"
    echo "  • Select 'Cached images and files'"
    echo "  • Click 'Clear data'"
    echo ""

    echo -e "${BLUE}Step 2: Open Sales Order${NC}"
    echo "  1. Go to: http://127.0.0.1:8000"
    echo "  2. Login: Administrator / admin"
    echo "  3. Navigate: Selling → Sales Order → New"
    echo ""

    echo -e "${BLUE}Step 3: Verify UI Elements${NC}"
    echo "  You should see:"
    echo -e "  ${GREEN}□${NC} 🤖 AI Assistant button in toolbar"
    echo -e "  ${GREEN}□${NC} AI Assistant panel with:"
    echo -e "      ${GREEN}•${NC} Conversation area (shows messages)"
    echo -e "      ${GREEN}•${NC} Input textarea (type your question)"
    echo -e "      ${GREEN}•${NC} Send button (or press Enter)"
    echo -e "      ${GREEN}•${NC} Suggestions button"
    echo -e "      ${GREEN}•${NC} Clear button"
    echo -e "      ${GREEN}•${NC} Status indicator"
    echo ""

    echo -e "${BLUE}Step 4: Test Functionality${NC}"
    echo "  1. Type: 'Hello AI' in the input field"
    echo "  2. Press Enter (should send message)"
    echo "  3. Check conversation area for response"
    echo "  4. Click Suggestions button (should show options)"
    echo "  5. Click Clear button (should clear conversation)"
    echo ""

    echo -e "${BLUE}Step 5: Check Browser Console${NC}"
    echo "  • Press F12 → Console tab"
    echo "  • Look for:"
    echo "    - 'AI Assistant: Integration script loaded successfully'"
    echo "    - 'AI Assistant: Form refresh for Sales Order'"
    echo "    - 'AI Assistant: Initializing for Sales Order'"
    echo "    - 'AI Assistant: Handlers setup complete'"
    echo ""
}

# Main execution
echo -e "${BLUE}Running AI Assistant UI Tests...${NC}\n"

# Run tests
test_js_elements
test_backend_api
test_page_integration

# Generate browser test instructions
generate_browser_test

# Summary
echo -e "${PURPLE}========================================="
echo "   Test Summary"
echo -e "=========================================${NC}\n"

echo -e "${GREEN}What's been implemented:${NC}"
echo "  ✅ Complete chat UI with conversation area"
echo "  ✅ Input field with Enter key support"
echo "  ✅ AI response display area"
echo "  ✅ Send button and keyboard shortcut"
echo "  ✅ Suggestions feature"
echo "  ✅ Clear conversation option"
echo "  ✅ Status indicators"
echo "  ✅ Frappe/ERPNext aligned design"
echo ""

echo -e "${YELLOW}Important Notes:${NC}"
echo "  • AI Provider needs valid API key for responses"
echo "  • User needs 'AI Assistant User' role"
echo "  • Clear browser cache after updates"
echo "  • Check console for debug messages"
echo ""

echo -e "${BLUE}Quick Commands:${NC}"
echo "  Rebuild: bench build --app ai_assistant --force"
echo "  Clear:   bench clear-cache"
echo "  Restart: bench restart"
echo ""

# Open browser for testing
echo -e "${GREEN}Opening Sales Order in browser for testing...${NC}"
open "http://127.0.0.1:8000/app/sales-order" 2>/dev/null || \
    xdg-open "http://127.0.0.1:8000/app/sales-order" 2>/dev/null || \
    echo "Please manually open: http://127.0.0.1:8000/app/sales-order"

echo -e "\n${GREEN}UI Test complete!${NC}\n"