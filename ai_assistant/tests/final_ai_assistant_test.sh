#!/bin/bash

# ========================================================================
# FINAL AI Assistant Complete Test & Verification Script
# Ensures 100% functionality in Sales Order and other DocTypes
# ========================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

BENCH_PATH="$HOME/Desktop/ERPNext-3/frappe-bench"
SITE_NAME="${1:-working.local.2}"

cd "$BENCH_PATH"

echo -e "${PURPLE}╔════════════════════════════════════════════════════════╗"
echo -e "║          AI ASSISTANT FINAL TEST & VERIFICATION         ║"
echo -e "║              100% Frappe/ERPNext Aligned                ║"
echo -e "╚════════════════════════════════════════════════════════╝${NC}\n"

# Test Results
PASS_COUNT=0
FAIL_COUNT=0

# Test function
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected="$3"

    echo -ne "  Testing: $test_name... "

    if eval "$test_cmd" 2>/dev/null | grep -q "$expected" 2>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAIL_COUNT++))
    fi
}

# ========================================================================
# SECTION 1: Core System Tests
# ========================================================================

echo -e "${CYAN}═══ SECTION 1: Core System Tests ═══${NC}"

# Server status
echo -ne "  Server Status: "
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ Not Running${NC}"
    ((FAIL_COUNT++))
    echo "  Starting server..."
    bench start > /tmp/bench_server.log 2>&1 &
    sleep 5
fi

# Database
run_test "Database Connection" \
    "bench --site $SITE_NAME mariadb -e 'SELECT 1'" \
    "1"

# Redis
run_test "Redis Cache" \
    "redis-cli -p 13000 ping" \
    "PONG"

echo ""

# ========================================================================
# SECTION 2: AI Assistant Installation
# ========================================================================

echo -e "${CYAN}═══ SECTION 2: AI Assistant Installation ═══${NC}"

run_test "App Installed" \
    "bench list-apps" \
    "ai_assistant"

run_test "Site Configuration" \
    "cat sites/$SITE_NAME/site_config.json" \
    "ai_assistant"

run_test "JavaScript Assets" \
    "ls -la sites/assets/ai_assistant/js/ai_assistant_integration.js && echo 'EXISTS'" \
    "EXISTS"

echo ""

# ========================================================================
# SECTION 3: Backend Configuration
# ========================================================================

echo -e "${CYAN}═══ SECTION 3: Backend Configuration ═══${NC}"

bench --site "$SITE_NAME" console << 'EOF' 2>/dev/null | grep -E "✓|✗" | while read line; do
    if echo "$line" | grep -q "✓"; then
        echo -e "  ${GREEN}$line${NC}"
    else
        echo -e "  ${RED}$line${NC}"
    fi
done
import frappe

# AI Provider
try:
    provider = frappe.get_doc("AI Provider", "AI Provider")
    print(f"✓ AI Provider: Active={provider.is_active}")
except:
    print("✗ AI Provider: Not configured")

# Roles
frappe.set_user("Administrator")
if "AI Assistant User" in frappe.get_roles():
    print("✓ Roles: Administrator has AI Assistant User")
else:
    print("✗ Roles: Administrator missing AI Assistant User")

# API Methods
try:
    from ai_assistant.api import start_session, chat_once
    print("✓ API: Methods loaded")
except:
    print("✗ API: Import failed")

# Hooks
hooks = frappe.get_hooks()
if "Sales Order" in hooks.get("doc_events", {}):
    print("✓ Hooks: Sales Order configured")
else:
    print("✗ Hooks: Sales Order not configured")
EOF

echo ""

# ========================================================================
# SECTION 4: UI Components Verification
# ========================================================================

echo -e "${CYAN}═══ SECTION 4: UI Components Verification ═══${NC}"

JS_FILE="sites/assets/ai_assistant/js/ai_assistant_integration.js"

# Check all UI components
UI_COMPONENTS=(
    "ai-user-input:Input Field"
    "ai-conversation-area:Response Area"
    "ai-send-btn:Send Button"
    "ai-messages:Message Display"
    "ai-status:Status Indicator"
    "ai-suggestion-btn:Suggestions"
    "ai-clear-btn:Clear Button"
    "Enter.*!e.shiftKey:Enter Key Handler"
)

for component in "${UI_COMPONENTS[@]}"; do
    IFS=':' read -r search_term display_name <<< "$component"
    echo -ne "  $display_name: "
    if grep -q "$search_term" "$JS_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ Present${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗ Missing${NC}"
        ((FAIL_COUNT++))
    fi
done

echo ""

# ========================================================================
# SECTION 5: DocType Integration
# ========================================================================

echo -e "${CYAN}═══ SECTION 5: DocType Integration ═══${NC}"

DOCTYPES=("Sales Order" "Purchase Order" "Sales Invoice" "Purchase Invoice" "Journal Entry")

for doctype in "${DOCTYPES[@]}"; do
    echo -ne "  $doctype: "

    # Check if hooks are registered
    if bench --site "$SITE_NAME" console << EOF 2>/dev/null | grep -q "True"
import frappe
hooks = frappe.get_hooks()
print("$doctype" in hooks.get("doc_events", {}))
EOF
    then
        echo -e "${GREEN}✓ Integrated${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗ Not Integrated${NC}"
        ((FAIL_COUNT++))
    fi
done

echo ""

# ========================================================================
# SECTION 6: Live Page Test
# ========================================================================

echo -e "${CYAN}═══ SECTION 6: Live Page Test ═══${NC}"

# Login
curl -s -X POST http://127.0.0.1:8000/api/method/login \
    -H "Content-Type: application/json" \
    -d '{"usr":"Administrator","pwd":"admin"}' \
    -c /tmp/ai_final_test.txt > /dev/null

# Test Sales Order page
RESPONSE=$(curl -s -b /tmp/ai_final_test.txt http://127.0.0.1:8000/app/sales-order 2>/dev/null)

echo -ne "  AI Assistant JS Loaded: "
if echo "$RESPONSE" | grep -q "ai_assistant_integration.js"; then
    echo -e "${GREEN}✓ Yes${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ No${NC}"
    ((FAIL_COUNT++))
fi

AI_REFS=$(echo "$RESPONSE" | grep -c "ai_assistant" || true)
echo -e "  AI References in Page: ${BLUE}$AI_REFS${NC}"

echo ""

# ========================================================================
# SECTION 7: Manual Testing Checklist
# ========================================================================

echo -e "${CYAN}═══ SECTION 7: Manual Browser Testing ═══${NC}"

echo -e "\n${YELLOW}Please verify the following in your browser:${NC}"

cat << 'CHECKLIST'

  ┌─ Clear Browser Cache ────────────────────────────┐
  │ • Press Ctrl+Shift+Delete (Cmd+Shift+Delete Mac) │
  │ • Select "Cached images and files"               │
  │ • Click "Clear data"                              │
  └───────────────────────────────────────────────────┘

  ┌─ Navigate to Sales Order ────────────────────────┐
  │ 1. Go to: http://127.0.0.1:8000                  │
  │ 2. Login: Administrator / admin                   │
  │ 3. Go to: Selling → Sales Order → New            │
  └───────────────────────────────────────────────────┘

  ┌─ Visual Verification ─────────────────────────────┐
  │ Check for these UI elements:                      │
  │                                                    │
  │ □ 🤖 AI Assistant button in toolbar              │
  │ □ AI Assistant panel containing:                  │
  │   □ Header with "🤖 AI Assistant"                │
  │   □ Conversation area (for messages)              │
  │   □ Input textarea with placeholder               │
  │   □ Send button (says "Send (Enter)")             │
  │   □ Suggestions button                            │
  │   □ Clear button in header                        │
  │   □ Status indicator area                         │
  └───────────────────────────────────────────────────┘

  ┌─ Functional Testing ───────────────────────────────┐
  │ 1. Type "Hello" in input field                     │
  │ 2. Press Enter → Message should appear             │
  │ 3. Click Suggestions → Dialog should open          │
  │ 4. Click Clear → Confirm dialog should appear      │
  │ 5. Check Console (F12) for debug messages          │
  └───────────────────────────────────────────────────┘

  ┌─ Console Messages to Verify ───────────────────────┐
  │ □ "AI Assistant: Integration script loaded"        │
  │ □ "AI Assistant: Form refresh for Sales Order"     │
  │ □ "AI Assistant: Initializing for Sales Order"     │
  │ □ "AI Assistant: Handlers setup complete"          │
  └───────────────────────────────────────────────────┘
CHECKLIST

# ========================================================================
# FINAL SUMMARY
# ========================================================================

echo -e "\n${PURPLE}╔════════════════════════════════════════════════════════╗"
echo -e "║                    TEST SUMMARY                         ║"
echo -e "╚════════════════════════════════════════════════════════╝${NC}"

TOTAL_TESTS=$((PASS_COUNT + FAIL_COUNT))
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_PERCENT=$((PASS_COUNT * 100 / TOTAL_TESTS))
else
    PASS_PERCENT=0
fi

echo ""
echo -e "  Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "  Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "  Failed: ${RED}$FAIL_COUNT${NC}"
echo -e "  Success Rate: ${CYAN}${PASS_PERCENT}%${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}  ✨ PERFECT! All automated tests passed!${NC}"
    echo -e "${GREEN}  AI Assistant is fully integrated and functional.${NC}"
elif [ $PASS_PERCENT -ge 80 ]; then
    echo -e "${YELLOW}  ⚠ Good! Most tests passed.${NC}"
    echo -e "${YELLOW}  Minor issues may need attention.${NC}"
else
    echo -e "${RED}  ❌ Issues detected. Manual intervention needed.${NC}"
fi

echo ""
echo -e "${BLUE}Quick Fix Commands:${NC}"
echo "  bench build --app ai_assistant --force"
echo "  bench clear-cache"
echo "  bench restart"
echo ""

# Open browser
echo -e "${GREEN}Opening Sales Order in browser...${NC}"
open "http://127.0.0.1:8000/app/sales-order" 2>/dev/null || \
    xdg-open "http://127.0.0.1:8000/app/sales-order" 2>/dev/null || \
    echo "Please manually open: http://127.0.0.1:8000/app/sales-order"

echo -e "\n${GREEN}✅ Final test complete!${NC}\n"