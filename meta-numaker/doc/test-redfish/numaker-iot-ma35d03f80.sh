#!/bin/bash

# --- Configuration Area ---
BMC_IP="numaker-iot-ma35d03f80.local"  # mDNS hostname (avahi)
USER="root"
PASS="0penBmc"
REPORT_FILE="$(dirname "$0")/numaker-iot-ma35d03f80.md"
# -------------------------

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Initialize report file
cat > "$REPORT_FILE" << EOF
# MA35D03F80 OpenBMC Functions Integration Test Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**BMC IP**: ${BMC_IP}
**Platform**: NuMaker-IoT-MA35D03F80

---

EOF

# Report helper: append to report
report() {
    echo -e "$1" >> "$REPORT_FILE"
}

report "## Test Results\n"

echo -e "${BLUE}====================================================${NC}"
echo -e "     MA35D03F80 OpenBMC Functions Integration Test    "
echo -e "${BLUE}====================================================${NC}"

# Function to run Redfish GET
run_get() {
    local endpoint=$1
    local name=$2
    echo -e "\n${BLUE}[Test] GET ${name}...${NC}"

    local response
    response=$(curl -k -s -u "${USER}:${PASS}" \
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

    local response
    response=$(curl -k -s -u "${USER}:${PASS}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "${data}" \
        -w "\n%{http_code}" \
        "https://${BMC_IP}${endpoint}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ] || [ "$http_code" -eq 204 ]; then
        echo -e "${GREEN}✓ Action Success (HTTP ${http_code})${NC}"
        report "- **POST ${name}**: ✓ HTTP ${http_code}"
        if [ -n "$body" ]; then
            if command -v jq &> /dev/null; then
                echo "$body" | jq '.'
            else
                echo "$body"
            fi
        fi
    else
        echo -e "${RED}✗ Action Failed! HTTP Code: ${http_code}${NC}"
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

    local response
    response=$(curl -k -s -u "${USER}:${PASS}" \
        -X PATCH \
        -H "Content-Type: application/json" \
        -d "${data}" \
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

# 1. Test Service Root
run_get "/redfish/v1/" "Service Root"

# 2. Test Chassis Collection
run_get "/redfish/v1/Chassis" "Chassis Collection"

# 3. Test Chassis Details (with retry for entity-manager startup delay)
echo -e "\n${BLUE}[Test] GET Chassis Details (system)...${NC}"
CHASSIS_RETRIES=5
CHASSIS_OK=0
for i in $(seq 1 $CHASSIS_RETRIES); do
    HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Chassis/system")
    if [ "$HTTP_CODE" -eq 200 ]; then
        CHASSIS_OK=1
        break
    fi
    echo -e "  ${YELLOW}Waiting for entity-manager... (attempt ${i}/${CHASSIS_RETRIES})${NC}"
    sleep 3
done
if [ "$CHASSIS_OK" -eq 1 ]; then
    run_get "/redfish/v1/Chassis/system" "Chassis Details (system)"
else
    echo -e "${RED}✗ Chassis/system not available after ${CHASSIS_RETRIES} retries${NC}"
    report "- **GET Chassis Details (system)**: ✗ HTTP ${HTTP_CODE} (after ${CHASSIS_RETRIES} retries)"
fi

# 4. Test Systems details & LocationIndicatorActive
run_get "/redfish/v1/Systems/system" "System details"

# 5. Toggle Identify LED (PN4) to Blink (LocationIndicatorActive = true)
echo -e "\n${YELLOW}>>> Action: Enabling Identify LED (PN4 Blink) <<<${NC}"
run_patch "/redfish/v1/Systems/system" "Set LocationIndicatorActive=true" '{"LocationIndicatorActive": true}'
sleep 3

# 6. Verify that it was enabled
run_get "/redfish/v1/Systems/system" "Verify LocationIndicatorActive state" | grep -E '"LocationIndicatorActive"' || true

# 7. Turn off Identify LED (PN4)
echo -e "\n${YELLOW}>>> Action: Disabling Identify LED (PN4 Off) <<<${NC}"
run_patch "/redfish/v1/Systems/system" "Set LocationIndicatorActive=false" '{"LocationIndicatorActive": false}'

# 8. Check SSH console capability description
echo -e "\n${BLUE}[Manual Verification Info]${NC}"
echo -e "To verify physical D-Bus & Sysfs status of the Identify LED during blinking:"
echo -e "1. SSH into the BMC: ${GREEN}ssh root@${BMC_IP}${NC} (Password: ${GREEN}${PASS}${NC})"
echo -e "2. Check D-Bus:      ${GREEN}busctl get-property xyz.openbmc_project.LED.Controller /xyz/openbmc_project/led/physical/front_id xyz.openbmc_project.Led.Physical State${NC}"
echo -e "3. Check Kernel trigger: ${GREEN}cat /sys/class/leds/front_id/trigger${NC} (Should show ${YELLOW}[timer]${NC})"

echo -e "\n${BLUE}====================================================${NC}"
echo -e "      Real-time Device Status / Logs / Power Tests     "
echo -e "${BLUE}====================================================${NC}"

# --- Real-time Access to Device Status ---
echo -e "\n${YELLOW}>>> Section: Real-time Access to Device Status <<<${NC}"

# 9. BMC Manager Status
run_get "/redfish/v1/Managers/bmc" "BMC Manager Status"

# 10. BMC State (PowerState, Health, FirmwareVersion)
echo -e "\n${BLUE}[Test] Verify BMC key status fields...${NC}"
response=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Managers/bmc")
if command -v jq &> /dev/null; then
    power_state=$(echo "$response" | jq -r '.PowerState // "N/A"')
    health=$(echo "$response" | jq -r '.Status.Health // "N/A"')
    fw_ver=$(echo "$response" | jq -r '.FirmwareVersion // "N/A"')
    echo -e "  PowerState:      ${GREEN}${power_state}${NC}"
    echo -e "  Health:          ${GREEN}${health}${NC}"
    echo -e "  FirmwareVersion: ${GREEN}${fw_ver}${NC}"
else
    echo "$response"
fi

# 11. System/Host Status
run_get "/redfish/v1/Systems/system" "System/Host Status (PowerState, Health)"
echo -e "\n${BLUE}[Test] Verify System key status fields...${NC}"
response=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system")
if command -v jq &> /dev/null; then
    sys_power=$(echo "$response" | jq -r '.PowerState // "N/A"')
    sys_health=$(echo "$response" | jq -r '.Status.Health // "N/A"')
    sys_state=$(echo "$response" | jq -r '.Status.State // "N/A"')
    echo -e "  PowerState: ${GREEN}${sys_power}${NC}"
    echo -e "  Health:     ${GREEN}${sys_health}${NC}"
    echo -e "  State:      ${GREEN}${sys_state}${NC}"
else
    echo "$response"
fi

# 12. Thermal Subsystem (new Redfish model)
run_get "/redfish/v1/Chassis/system/ThermalSubsystem" "Chassis ThermalSubsystem"

# 13. Power Subsystem (new Redfish model)
run_get "/redfish/v1/Chassis/system/PowerSubsystem" "Chassis PowerSubsystem"

# 14. Sensor Collection via TelemetryService or Chassis Sensors
run_get "/redfish/v1/Chassis/system/Sensors" "Chassis Sensor Collection"

# --- System Logs ---
echo -e "\n${YELLOW}>>> Section: System Logs <<<${NC}"

# 15. BMC Log Service collection
run_get "/redfish/v1/Managers/bmc/LogServices" "BMC Log Services Collection"

# 16. BMC Journal Entries (event log)
run_get "/redfish/v1/Managers/bmc/LogServices/Journal/Entries?\$top=5" "BMC Journal Entries (latest 5)"

# 17. System Event Log
run_get "/redfish/v1/Systems/system/LogServices" "System Log Services Collection"

# 18. System Event Log Entries
run_get "/redfish/v1/Systems/system/LogServices/EventLog/Entries?\$top=5" "System EventLog Entries (latest 5)"

# 19. Redfish Event Service status
run_get "/redfish/v1/EventService" "Event Service Status"

# --- User Management (phosphor-user-manager / AccountService) ---
echo -e "\n${YELLOW}>>> Section: User Management <<<${NC}"
report "\n### User Management\n"

TEST_USER="rftestuser"
TEST_PASS="TestPass123"

# 20. AccountService root
run_get "/redfish/v1/AccountService" "AccountService Root"

# 21. Accounts collection (should include root)
run_get "/redfish/v1/AccountService/Accounts" "Accounts Collection"

# 22. Create a test local account
run_post "/redfish/v1/AccountService/Accounts" \
    "Create Test Account (${TEST_USER})" \
    "{\"UserName\": \"${TEST_USER}\", \"Password\": \"${TEST_PASS}\", \"RoleId\": \"Operator\"}"
sleep 2

# 23. Verify the new account exists
run_get "/redfish/v1/AccountService/Accounts/${TEST_USER}" "Verify New Account (${TEST_USER})"

# 24. Login as the new local account (verify local PAM auth works)
echo -e "\n${BLUE}[Test] Login as new local account (${TEST_USER})...${NC}"
LOGIN_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${TEST_USER}:${TEST_PASS}" "https://${BMC_IP}/redfish/v1/Systems/system")
if [ "$LOGIN_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Login Success (HTTP 200)${NC}"
    report "- **Login as ${TEST_USER}**: ✓ HTTP 200"
else
    echo -e "${RED}✗ Login Failed! HTTP Code: ${LOGIN_CODE}${NC}"
    report "- **Login as ${TEST_USER}**: ✗ HTTP ${LOGIN_CODE}"
fi

# 25. Change role (Operator -> ReadOnly)
run_patch "/redfish/v1/AccountService/Accounts/${TEST_USER}" \
    "Change Role to ReadOnly" '{"RoleId": "ReadOnly"}'

# 26. Disable the account, then verify login is rejected
run_patch "/redfish/v1/AccountService/Accounts/${TEST_USER}" \
    "Disable Account" '{"Enabled": false}'
sleep 1
echo -e "\n${BLUE}[Test] Verify disabled account is rejected...${NC}"
DISABLED_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${TEST_USER}:${TEST_PASS}" "https://${BMC_IP}/redfish/v1/Systems/system")
if [ "$DISABLED_CODE" -eq 401 ]; then
    echo -e "${GREEN}✓ Disabled account correctly rejected (HTTP 401)${NC}"
    report "- **Verify Disabled Account Rejected**: ✓ HTTP 401"
else
    echo -e "${RED}✗ Unexpected HTTP Code: ${DISABLED_CODE} (expected 401)${NC}"
    report "- **Verify Disabled Account Rejected**: ✗ HTTP ${DISABLED_CODE} (expected 401)"
fi

# 27. Delete the test account and verify removal
run_delete "/redfish/v1/AccountService/Accounts/${TEST_USER}" "Delete Test Account (${TEST_USER})"
sleep 1
echo -e "\n${BLUE}[Test] Verify test account removed...${NC}"
GONE_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/AccountService/Accounts/${TEST_USER}")
if [ "$GONE_CODE" -eq 404 ]; then
    echo -e "${GREEN}✓ Account successfully removed (HTTP 404)${NC}"
    report "- **Verify Account Removed**: ✓ HTTP 404"
else
    echo -e "${RED}✗ Unexpected HTTP Code: ${GONE_CODE} (expected 404)${NC}"
    report "- **Verify Account Removed**: ✗ HTTP ${GONE_CODE} (expected 404)"
fi

# 28. Confirm LDAP remote user management is NOT functionally enabled
#     (trimmed for 256MB platform). Note: bmcweb always exposes a static
#     "LDAP" stub (just a link to /LDAP/Certificates) per the Redfish schema
#     even when nss-pam-ldapd/phosphor-ldap aren't installed, so checking for
#     the field's mere presence is not a valid test. Check for the
#     "ServiceEnabled"/"Authentication" sub-properties instead, which are only
#     populated when phosphor-ldap is actually installed and functional.
echo -e "\n${BLUE}[Test] Verify LDAP backend is not functionally configured (expected)...${NC}"
response=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/AccountService")
if command -v jq &> /dev/null; then
    ldap_configured=$(echo "$response" | jq -r '.LDAP | has("ServiceEnabled") or has("Authentication")')
    echo -e "  LDAP functionally configured: ${YELLOW}${ldap_configured}${NC}"
    report "- **LDAP Functionally Configured**: ${ldap_configured} (expected: false)"
else
    echo "$response" | grep -o '"ServiceEnabled"\|"Authentication"' || echo "  LDAP backend not configured (expected)"
fi

# --- Power Controls ---
echo -e "\n${YELLOW}>>> Section: Power Controls <<<${NC}"
report "\n### Power Controls\n"

# Pre-flight: Ensure BMC is in Ready state and power-control is running.
echo -e "\n${BLUE}[Pre-flight] Ensuring BMC Ready state for power tests...${NC}"
BMC_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Managers/bmc" | jq -r '.Status.State // "N/A"')
if [ "$BMC_STATE" != "Enabled" ]; then
    echo -e "${YELLOW}BMC not Ready (State: ${BMC_STATE}), waiting...${NC}"
    sleep 10
    BMC_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Managers/bmc" | jq -r '.Status.State // "N/A"')
fi
echo -e "  BMC State: ${GREEN}${BMC_STATE}${NC}"

# 29. Check current Chassis power state before actions
run_get "/redfish/v1/Chassis/system" "Chassis Power State (before action)"

# --- Power On Test ---
report "\n### Power Control Tests\n"

# 30. Host Power On
echo -e "\n${YELLOW}>>> Action: Request Host Power On <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ POWER ON: After sending command, connect PK12 (PS_PWROK)│${NC}"
echo -e "${RED}│     to 3.3V HIGH (simulate Host PSU Power Good)            │${NC}"
echo -e "${RED}│     Wiring: PK12 → VDD 3.3V or motherboard PWR_LED+       │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  Press Enter to confirm PK12=HIGH is ready (or PWR_LED+ connected)..."
report "- **Power On**: Operator prompted to connect PK12 to HIGH"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host Power On" \
    '{"ResetType": "On"}'
sleep 5

# 31. Verify host power state after power on
echo -e "\n${BLUE}[Verify] Confirm PK12 (PS_PWROK) reads HIGH → Chassis=On${NC}"
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after Power On"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Power On**: PowerState=${POWER_STATE}"

# --- Force Off Test ---
# 32. Host ForceOff
echo -e "\n${YELLOW}>>> Action: Request Host ForceOff <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ FORCE OFF: After sending command, disconnect PK12      │${NC}"
echo -e "${RED}│     (PS_PWROK) from 3.3V (remove PWR_LED+ wire)            │${NC}"
echo -e "${RED}│     PK12 should return to LOW (0V) via pull-down resistor  │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  Press Enter to confirm ready to set PK12=LOW after ForceOff..."
report "- **Force Off**: Operator prompted to disconnect PK12 to LOW"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host ForceOff" \
    '{"ResetType": "ForceOff"}'

echo -e "\n${YELLOW}  Waiting 4s for ForceOff pulse to complete...${NC}"
sleep 5
echo -e "${RED}  >>> Please confirm PK12 is now LOW (3.3V disconnected) <<<${NC}"
read -p "  Press Enter to confirm PK12 is LOW..."

# 33. Verify host power state after ForceOff
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after ForceOff"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Force Off**: PowerState=${POWER_STATE}"

# --- Force Restart Test ---
# 34. Host ForceRestart (from whatever current state)
echo -e "\n${YELLOW}>>> Action: Request Host ForceRestart <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ RESTART: RESET_OUT (PN0) will pulse LOW for 500ms      │${NC}"
echo -e "${RED}│     PK12 (PS_PWROK) should remain HIGH (Host stays on)     │${NC}"
echo -e "${RED}│     If PK12=LOW, connect HIGH first before continuing      │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  Press Enter to confirm PK12=HIGH (Host is powered on)..."
report "- **Force Restart**: Confirmed PK12=HIGH"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host ForceRestart" \
    '{"ResetType": "ForceRestart"}'
sleep 5

# 35. Verify host power state after restart
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after ForceRestart"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Force Restart**: PowerState=${POWER_STATE}"

# 36. Check supported ResetType values
echo -e "\n${BLUE}[Test] Query supported ResetType values...${NC}"
response=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system")
if command -v jq &> /dev/null; then
    echo "$response" | jq '.Actions."#ComputerSystem.Reset"'
else
    echo "$response"
fi

echo -e "\n${BLUE}====================================================${NC}"
echo -e "${GREEN}Integration Test Script Finished!${NC}"
echo -e "${BLUE}====================================================${NC}"

# Finalize report
report "\n---\n"
report "## Summary\n"
report "- Test completed at: $(date '+%Y-%m-%d %H:%M:%S')"
report "- Report file: ${REPORT_FILE}"
echo -e "\n${GREEN}Report saved to: ${REPORT_FILE}${NC}"
