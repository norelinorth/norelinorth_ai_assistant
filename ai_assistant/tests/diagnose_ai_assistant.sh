#!/bin/bash

# ========================================================================
# AI Assistant Diagnostic Script
# Diagnoses why AI Assistant might not be visible in Sales Order
# ========================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}========================================="
echo "   AI Assistant Diagnostic Report"
echo -e "=========================================${NC}\n"

cd ~/Desktop/ERPNext-3/frappe-bench

# 1. Check server status
echo -e "${YELLOW}1. Server Status:${NC}"
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Server running on port 8000"
    PID=$(lsof -ti:8000 | head -1)
    echo "  PID: $PID"
else
    echo -e "${RED}✗${NC} Server not running"
fi

# 2. Check JavaScript file
echo -e "\n${YELLOW}2. JavaScript Files:${NC}"
JS_FILE="sites/assets/ai_assistant/js/ai_assistant_integration.js"
if [ -f "$JS_FILE" ]; then
    SIZE=$(wc -c < "$JS_FILE")
    MODIFIED=$(stat -f "%Sm" "$JS_FILE" 2>/dev/null || stat -c "%y" "$JS_FILE" 2>/dev/null | cut -d' ' -f1-2)
    echo -e "${GREEN}✓${NC} $JS_FILE"
    echo "  Size: $SIZE bytes"
    echo "  Modified: $MODIFIED"

    # Check for console.log statements
    if grep -q "console.log" "$JS_FILE"; then
        echo -e "${GREEN}✓${NC} Debug logging enabled"
    fi
else
    echo -e "${RED}✗${NC} JavaScript file not found"
fi

# 3. Test page load
echo -e "\n${YELLOW}3. Testing Sales Order Page:${NC}"

# Login first
curl -s -X POST http://127.0.0.1:8000/api/method/login \
    -H "Content-Type: application/json" \
    -d '{"usr":"Administrator","pwd":"admin"}' \
    -c /tmp/ai_test_cookies.txt > /dev/null

# Get Sales Order page
RESPONSE=$(curl -s -b /tmp/ai_test_cookies.txt http://127.0.0.1:8000/app/sales-order/new-sales-order-1 2>/dev/null)

if echo "$RESPONSE" | grep -q "ai_assistant_integration.js"; then
    echo -e "${GREEN}✓${NC} AI Assistant JS referenced in page"
else
    echo -e "${RED}✗${NC} AI Assistant JS not referenced"
fi

if echo "$RESPONSE" | grep -q "AI Assistant"; then
    COUNT=$(echo "$RESPONSE" | grep -o "AI Assistant" | wc -l)
    echo -e "${GREEN}✓${NC} 'AI Assistant' text found $COUNT times"
else
    echo -e "${RED}✗${NC} 'AI Assistant' text not found"
fi

# 4. Check backend configuration
echo -e "\n${YELLOW}4. Backend Configuration:${NC}"

bench --site working.local.2 console << 'EOF' 2>/dev/null | grep -E "✓|✗|Active|Role"
import frappe

# Check AI Provider
try:
    provider = frappe.get_doc("AI Provider", "AI Provider")
    print(f"✓ AI Provider Active: {provider.is_active}")
except:
    print("✗ AI Provider not found")

# Check user role
frappe.set_user("Administrator")
roles = frappe.get_roles()
if "AI Assistant User" in roles:
    print("✓ Administrator has AI Assistant User role")
else:
    print("✗ Administrator missing role")

# Test hook function
try:
    from ai_assistant.doctype_hooks import inject_ai_assistant
    print("✓ Hook module loads successfully")
except ImportError:
    print("✗ Hook module import failed")
EOF

# 5. Browser Instructions
echo -e "\n${PURPLE}========================================="
echo "   Browser Verification Steps"
echo -e "=========================================${NC}\n"

echo -e "${BLUE}Step 1: Clear Browser Cache${NC}"
echo "  • Chrome/Edge: Ctrl+Shift+Delete → Clear browsing data"
echo "  • Firefox: Ctrl+Shift+Delete → Clear Recent History"
echo "  • Safari: Develop menu → Empty Caches"
echo ""

echo -e "${BLUE}Step 2: Open Browser Console${NC}"
echo "  • Press F12 or right-click → Inspect"
echo "  • Go to Console tab"
echo "  • Look for messages starting with 'AI Assistant:'"
echo ""

echo -e "${BLUE}Step 3: Navigate to Sales Order${NC}"
echo "  1. Go to: http://127.0.0.1:8000"
echo "  2. Login: Administrator / admin"
echo "  3. Go to: Selling → Sales Order"
echo "  4. Click: New Sales Order"
echo ""

echo -e "${BLUE}Step 4: Check Console Output${NC}"
echo "  You should see:"
echo "  • 'AI Assistant: Integration script loaded'"
echo "  • 'AI Assistant: Sales Order form loaded'"
echo "  • 'AI Assistant: Sales Order form refreshed'"
echo ""

echo -e "${BLUE}Step 5: Look for AI Assistant${NC}"
echo "  • Check 'Actions' dropdown menu"
echo "  • Look for 'AI Assistant' button"
echo "  • Check dashboard panel area"
echo ""

# 6. Quick Fix Commands
echo -e "${PURPLE}========================================="
echo "   Quick Fix Commands"
echo -e "=========================================${NC}\n"

echo "If AI Assistant is still not visible, run:"
echo -e "${YELLOW}"
echo "cd ~/Desktop/ERPNext-3/frappe-bench"
echo "bench clear-cache"
echo "bench build --app ai_assistant --force"
echo "# Then clear browser cache completely"
echo -e "${NC}"

echo -e "\n${GREEN}Diagnostic complete!${NC}\n"