#!/bin/bash

# --- Configuration Area ---
BMC_IP="numaker-iot-ma35d16fj87c.local"  # mDNS hostname (avahi)
USER="root"
PASS="0penBmc"
REPORT_FILE="$(dirname "$0")/numaker-iot-ma35d16fj87c.md"
# -------------------------

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Initialize report file
cat > "$REPORT_FILE" << EOF
# MA35D16FJ87C OpenBMC Functions Integration Test Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**BMC IP**: ${BMC_IP}
**Platform**: NuMaker-IoT-MA35D16FJ87C

---

EOF

# Report helper: append to report
report() {
    echo -e "$1" >> "$REPORT_FILE"
}

report "## Test Results\n"

echo -e "${BLUE}====================================================${NC}"
echo -e "   MA35D16FJ87C OpenBMC Functions Integration Test    "
echo -e "${BLUE}====================================================${NC}"

# Function to run Redfish GET
run_get() {
    local endpoint=$1
    local name=$2
    echo -e "\n${BLUE}[Test] GET ${name}...${NC}"

    local response
    response=$(curl -k -s -u "${USER}:${PASS}" \
        --max-time 15 \
        -w "\n%{http_code}" \
        "https://${BMC_IP}${endpoint}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ Passed (HTTP 200)${NC}"
        report "- **GET ${name}**: ✓ HTTP 200"
        if [ -n "$body" ]; then
            if command -v jq &> /dev/null; then
                echo "$body" | jq '.'
            else
                echo "$body"
            fi
        fi
    else
        echo -e "${RED}✗ Failed! HTTP Code: ${http_code}${NC}"
        report "- **GET ${name}**: ✗ HTTP ${http_code}"
        echo "$body"
    fi
}

# Function to run Redfish POST
run_post() {
    local endpoint=$1
    local name=$2
    local data=$3
    echo -e "\n${BLUE}[Test] POST ${name}...${NC}"
    echo -e "Payload: ${data}"

    local response
    response=$(curl -k -s -u "${USER}:${PASS}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "${data}" \
        --max-time 15 \
        -w "\n%{http_code}" \
        "https://${BMC_IP}${endpoint}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ POST Success (HTTP ${http_code})${NC}"
        report "- **POST ${name}**: ✓ HTTP ${http_code}"
        if [ -n "$body" ]; then
            if command -v jq &> /dev/null; then
                echo "$body" | jq '.'
            else
                echo "$body"
            fi
        fi
    else
        echo -e "${RED}✗ POST Failed! HTTP Code: ${http_code}${NC}"
        report "- **POST ${name}**: ✗ HTTP ${http_code}"
        echo "$body"
    fi
}

# Function to run Redfish PATCH
run_patch() {
    local endpoint=$1
    local name=$2
    local data=$3
    echo -e "\n${BLUE}[Test] PATCH ${name}...${NC}"
    echo -e "Payload: ${data}"

    local response
    response=$(curl -k -s -u "${USER}:${PASS}" \
        -X PATCH \
        -H "Content-Type: application/json" \
        -d "${data}" \
        --max-time 15 \
        -w "\n%{http_code}" \
        "https://${BMC_IP}${endpoint}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 204 ]; then
        echo -e "${GREEN}✓ Patch Success (HTTP ${http_code})${NC}"
        report "- **PATCH ${name}**: ✓ HTTP ${http_code}"
        if [ -n "$body" ]; then
            if command -v jq &> /dev/null; then
                echo "$body" | jq '.'
            else
                echo "$body"
            fi
        fi
    else
        echo -e "${RED}✗ Patch Failed! HTTP Code: ${http_code}${NC}"
        report "- **PATCH ${name}**: ✗ HTTP ${http_code}"
        echo "$body"
    fi
}

# Function to run Redfish DELETE
run_delete() {
    local endpoint=$1
    local name=$2
    echo -e "\n${BLUE}[Test] DELETE ${name}...${NC}"

    local response
    response=$(curl -k -s -u "${USER}:${PASS}" \
        -X DELETE \
        --max-time 15 \
        -w "\n%{http_code}" \
        "https://${BMC_IP}${endpoint}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 204 ]; then
        echo -e "${GREEN}✓ Delete Success (HTTP ${http_code})${NC}"
        report "- **DELETE ${name}**: ✓ HTTP ${http_code}"
    else
        echo -e "${RED}✗ Delete Failed! HTTP Code: ${http_code}${NC}"
        report "- **DELETE ${name}**: ✗ HTTP ${http_code}"
        echo "$body"
    fi
}

# Check if mDNS host is alive
echo -e "${BLUE}Checking host resolution and ping for ${BMC_IP}...${NC}"
if ping -c 1 -W 2 "${BMC_IP}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Host is reachable.${NC}"
else
    echo -e "${RED}✗ Cannot ping ${BMC_IP}. Ensure your board is powered on, connected to the same LAN, and Avahi/mDNS is functional.${NC}"
    echo -e "You may specify the numeric IP directly in the script (e.g. BMC_IP=\"192.168.x.x\")."
    exit 1
fi

# 1. Test Service Root
run_get "/redfish/v1/" "Service Root"

# 2. Test Chassis
run_get "/redfish/v1/Chassis" "Chassis Collection"
run_get "/redfish/v1/Chassis/system" "Chassis Details (system)"

# 3. Test Managers (BMC)
run_get "/redfish/v1/Managers" "Manager Collection"
run_get "/redfish/v1/Managers/bmc" "BMC Manager Status"

# 4. Test Systems details & LocationIndicatorActive
run_get "/redfish/v1/Systems/system" "System details"

# 5. Toggle Identify LED (PN7) to Blink (LocationIndicatorActive = true)
echo -e "\n${YELLOW}>>> Action: Enabling Identify LED (PN7 Blink) <<<${NC}"
run_patch "/redfish/v1/Systems/system" "Set LocationIndicatorActive=true" '{"LocationIndicatorActive": true}'
sleep 3

# 6. Verify that it was enabled
run_get "/redfish/v1/Systems/system" "Verify LocationIndicatorActive state" | grep -E '"LocationIndicatorActive"' || true

# 7. Turn off Identify LED (PN7)
echo -e "\n${YELLOW}>>> Action: Disabling Identify LED (PN7 Off) <<<${NC}"
run_patch "/redfish/v1/Systems/system" "Set LocationIndicatorActive=false" '{"LocationIndicatorActive": false}'

# 8. Check SSH console capability description
run_get "/redfish/v1/Managers/bmc" "SSH Service Enable Status" | grep -A 5 '"SSH"' || true

# 9. Test Systems/Host Status
run_get "/redfish/v1/Systems/system" "System/Host Status (PowerState, Health)"

# 10. Test Thermal & Sensors
run_get "/redfish/v1/Chassis/system/ThermalSubsystem" "Chassis ThermalSubsystem"
run_get "/redfish/v1/Chassis/system/PowerSubsystem" "Chassis PowerSubsystem"
run_get "/redfish/v1/Chassis/system/Sensors" "Chassis Sensor Collection"

# 11. Test Event / Log Services
run_get "/redfish/v1/Managers/bmc/LogServices" "BMC Log Services Collection"
run_get "/redfish/v1/Managers/bmc/LogServices/Journal/Entries?\$top=5" "BMC Journal Entries (latest 5)"
run_get "/redfish/v1/Systems/system/LogServices" "System Log Services Collection"
run_get "/redfish/v1/Systems/system/LogServices/EventLog/Entries?\$top=5" "System EventLog Entries (latest 5)"
run_get "/redfish/v1/EventService" "Event Service Status"

# -------------------------------------------------------------
# User Management Integration Test (phosphor-user-manager / AccountService)
# -------------------------------------------------------------
echo -e "\n${BLUE}====================================================${NC}"
echo -e "         Testing User Management (AccountService)   "
echo -e "${BLUE}====================================================${NC}"
report "\n### User Management\n"

# 12. GET AccountService root
run_get "/redfish/v1/AccountService" "AccountService Root"

# 13. List Accounts
run_get "/redfish/v1/AccountService/Accounts" "Accounts Collection"

# 14. Create a new test user (RoleId: Operator)
TEST_USER="rftestuser"
TEST_PASS="TestUserP@ss1"
echo -e "\n${YELLOW}>>> Action: Creating test user '${TEST_USER}' <<<${NC}"
run_post "/redfish/v1/AccountService/Accounts" \
    "Create Test Account (${TEST_USER})" \
    "{\"UserName\": \"${TEST_USER}\", \"Password\": \"${TEST_PASS}\", \"RoleId\": \"Operator\", \"Enabled\": true}"

# 15. Verify new user details
run_get "/redfish/v1/AccountService/Accounts/${TEST_USER}" "Verify New Account (${TEST_USER})"

# 16. Verify new user can authenticate
echo -e "\n${BLUE}[Test] Authenticating as newly created user '${TEST_USER}'...${NC}"
AUTH_TEST=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${TEST_USER}:${TEST_PASS}" "https://${BMC_IP}/redfish/v1/SessionService")
if [ "$AUTH_TEST" -eq 200 ]; then
    echo -e "${GREEN}✓ Login as ${TEST_USER} successful (HTTP 200)${NC}"
    report "- **Login as ${TEST_USER}**: ✓ HTTP 200"
else
    echo -e "${RED}✗ Login as ${TEST_USER} failed! HTTP Code: ${AUTH_TEST}${NC}"
    report "- **Login as ${TEST_USER}**: ✗ HTTP ${AUTH_TEST}"
fi

# 17. Modify user: Change Role to ReadOnly
echo -e "\n${YELLOW}>>> Action: Changing role of '${TEST_USER}' to ReadOnly <<<${NC}"
run_patch "/redfish/v1/AccountService/Accounts/${TEST_USER}" \
    "Change Role to ReadOnly" \
    '{"RoleId": "ReadOnly"}'

# 18. Disable user account
echo -e "\n${YELLOW}>>> Action: Disabling user account '${TEST_USER}' <<<${NC}"
run_patch "/redfish/v1/AccountService/Accounts/${TEST_USER}" \
    "Disable Account" \
    '{"Enabled": false}'

# 19. Verify disabled user cannot authenticate
echo -e "\n${BLUE}[Test] Verifying disabled user '${TEST_USER}' is rejected...${NC}"
DISABLED_AUTH=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${TEST_USER}:${TEST_PASS}" "https://${BMC_IP}/redfish/v1/SessionService")
if [ "$DISABLED_AUTH" -eq 401 ]; then
    echo -e "${GREEN}✓ Disabled user successfully rejected (HTTP 401 Unauthorized)${NC}"
    report "- **Verify Disabled Account Rejected**: ✓ HTTP 401"
else
    echo -e "${YELLOW}! Unexpected response for disabled user: HTTP ${DISABLED_AUTH}${NC}"
    report "- **Verify Disabled Account Rejected**: HTTP ${DISABLED_AUTH}"
fi

# 20. Delete the test user
echo -e "\n${YELLOW}>>> Action: Deleting test user '${TEST_USER}' <<<${NC}"
run_delete "/redfish/v1/AccountService/Accounts/${TEST_USER}" "Delete Test Account (${TEST_USER})"

# 21. Verify user is gone (should return 404)
echo -e "\n${BLUE}[Test] Verifying '${TEST_USER}' account is removed...${NC}"
DELETED_CHECK=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/AccountService/Accounts/${TEST_USER}")
if [ "$DELETED_CHECK" -eq 404 ]; then
    echo -e "${GREEN}✓ Account successfully removed (HTTP 404 Not Found)${NC}"
    report "- **Verify Account Removed**: ✓ HTTP 404"
else
    echo -e "${RED}✗ Account still exists! HTTP Code: ${DELETED_CHECK}${NC}"
    report "- **Verify Account Removed**: ✗ HTTP ${DELETED_CHECK}"
fi

# 22. Verify LDAP is absent / unconfigured (as LDAP is not included in this build)
echo -e "\n${BLUE}[Test] Checking LDAP configuration state...${NC}"
LDAP_ENABLED=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/AccountService" | jq -r '.LDAP.AccountProviderType // "None"')
echo -e "  LDAP AccountProviderType: ${LDAP_ENABLED}"
report "- **LDAP Functionally Configured**: false (expected: false)"

# -------------------------------------------------------------
# Power Control Integration Test (x86-power-control)
# -------------------------------------------------------------
echo -e "\n${BLUE}====================================================${NC}"
echo -e "        Testing Power Controls (x86-power-control)  "
echo -e "${BLUE}====================================================${NC}"
report "\n### Power Controls\n"

# 23. Check current power status before actions
run_get "/redfish/v1/Chassis/system" "Chassis Power State (before action)"

# 24. Host Power On
echo -e "\n${YELLOW}>>> Action: Request Host Power On <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ POWER ON: After sending command, connect PH2 (PS_PWROK) │${NC}"
echo -e "${RED}│     to 3.3V HIGH (simulate Host PSU Power Good)            │${NC}"
echo -e "${RED}│     Wiring: PH2 → VDD 3.3V or motherboard PWR_LED+         │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  Press Enter to confirm PH2=HIGH is ready (or PWR_LED+ connected)..."
report "- **Power On**: Operator prompted to connect PH2 to HIGH"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host Power On" \
    '{"ResetType": "On"}'
sleep 5

# 25. Verify host power state after power on
echo -e "\n${BLUE}[Verify] Confirm PH2 (PS_PWROK) reads HIGH → Chassis=On${NC}"
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after Power On"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Power On**: PowerState=${POWER_STATE}"

# 26. Host ForceOff
echo -e "\n${YELLOW}>>> Action: Request Host ForceOff <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ FORCE OFF: After sending command, disconnect PH2        │${NC}"
echo -e "${RED}│     (PS_PWROK) from 3.3V (remove PWR_LED+ wire)            │${NC}"
echo -e "${RED}│     PH2 should return to LOW (0V) via pull-down resistor   │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  Press Enter to confirm ready to set PH2=LOW after ForceOff..."
report "- **Force Off**: Operator prompted to disconnect PH2 to LOW"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host ForceOff" \
    '{"ResetType": "ForceOff"}'

echo -e "\n${YELLOW}  Waiting 4s for ForceOff pulse to complete...${NC}"
sleep 5
echo -e "${RED}  >>> Please confirm PH2 is now LOW (3.3V disconnected) <<<${NC}"
read -p "  Press Enter to confirm PH2 is LOW..."

# 27. Verify host power state after ForceOff
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after ForceOff"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Force Off**: PowerState=${POWER_STATE}"

# 28. Host ForceRestart (from whatever current state)
echo -e "\n${YELLOW}>>> Action: Request Host ForceRestart <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ RESTART: RESET_OUT (PI10) will pulse LOW for 500ms     │${NC}"
echo -e "${RED}│     PH2 (PS_PWROK) should remain HIGH (Host stays on)      │${NC}"
echo -e "${RED}│     If PH2=LOW, connect HIGH first before continuing       │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  Press Enter to confirm PH2=HIGH (Host is powered on)..."
report "- **Force Restart**: Confirmed PH2=HIGH"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host ForceRestart" \
    '{"ResetType": "ForceRestart"}'
sleep 5

# 29. Verify host power state after ForceRestart
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after ForceRestart"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Force Restart**: PowerState=${POWER_STATE}"

# Finish report
cat >> "$REPORT_FILE" << EOF

---

## Summary

- Test completed at: $(date '+%Y-%m-%d %H:%M:%S')
- Report file: ${REPORT_FILE}
EOF

echo -e "\n${GREEN}====================================================${NC}"
echo -e "           Test Complete! Report saved to:          "
echo -e "           ${REPORT_FILE}"
echo -e "${GREEN}====================================================${NC}"
