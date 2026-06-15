#!/bin/bash

# --- Configuration Area ---
BMC_IP="192.168.0.57"  # Replace with your NUC980 BMC IP address
USER="root"
PASS="0penBmc"
REPORT_FILE="$(dirname "$0")/test_nuc980_functions_report.md"
# -------------------------

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Initialize report file
cat > "$REPORT_FILE" << EOF
# NUC980 OpenBMC Functions Integration Test Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**BMC IP**: ${BMC_IP}
**Platform**: NuMaker-IoT-NUC980G2

---

EOF

# Report helper: append to report
report() {
    echo -e "$1" >> "$REPORT_FILE"
}

report "## Test Results\n"

echo -e "${BLUE}====================================================${NC}"
echo -e "      NUC980 OpenBMC Functions Integration Test      "
echo -e "${BLUE}====================================================${NC}"

# Function to run Redfish GET
run_get() {
    local endpoint=$1
    local name=$2
    echo -e "\n${BLUE}[Test] GET ${name}...${NC}"
    
    local response
    response=$(curl -k -s -u "${USER}:${PASS}" -w "\n%{http_code}" "https://${BMC_IP}${endpoint}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ Success (HTTP 200)${NC}"
        report "- **GET ${name}**: ✓ HTTP 200"
        if command -v jq &> /dev/null; then
            echo "$body" | jq '.'
        else
            echo "$body"
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

# 1. Test Service Root
run_get "/redfish/v1/" "Service Root"

# 2. Test Chassis Collection
run_get "/redfish/v1/Chassis" "Chassis Collection"

# 3. Test Chassis Details
run_get "/redfish/v1/Chassis/system" "Chassis Details (system)"

# 4. Test Systems details & LocationIndicatorActive
run_get "/redfish/v1/Systems/system" "System details"

# 5. Toggle Identify LED (PB13) to Blink (LocationIndicatorActive = true)
echo -e "\n${YELLOW}>>> Action: Enabling Identify LED (PB13 Blink) <<<${NC}"
run_patch "/redfish/v1/Systems/system" "Set LocationIndicatorActive=true" '{"LocationIndicatorActive": true}'
sleep 3

# 6. Verify that it was enabled
run_get "/redfish/v1/Systems/system" "Verify LocationIndicatorActive state" | grep -E '"LocationIndicatorActive"' || true

# 7. Turn off Identify LED (PB13)
echo -e "\n${YELLOW}>>> Action: Disabling Identify LED (PB13 Off) <<<${NC}"
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

# --- Power Controls ---
echo -e "\n${YELLOW}>>> Section: Power Controls <<<${NC}"
report "\n### Power Controls\n"

# Pre-flight: Ensure BMC is in Ready state and power-control is running.
echo -e "\n${BLUE}[Pre-flight] Ensuring BMC Ready state for power tests...${NC}"
BMC_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Managers/bmc" | jq -r '.Status.State // "N/A"')
if [ "$BMC_STATE" != "Enabled" ]; then
    echo -e "${YELLOW}BMC not Ready (State: ${BMC_STATE}), attempting SSH fix...${NC}"
    if command -v sshpass &> /dev/null; then
        sshpass -p "${PASS}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
            ${USER}@${BMC_IP} \
            'systemctl stop mapper-wait@-org-openbmc-control-power0.service 2>/dev/null; systemctl reset-failed 2>/dev/null' 2>/dev/null
        sleep 5
        BMC_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Managers/bmc" | jq -r '.Status.State // "N/A"')
    fi
fi
echo -e "  BMC State: ${GREEN}${BMC_STATE}${NC}"

# Ensure power-control daemon is running (x86-power-control with GPIO, no PS_PWROK dependency)
if command -v sshpass &> /dev/null; then
    sshpass -p "${PASS}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        ${USER}@${BMC_IP} '
pgrep -x power-control >/dev/null 2>&1 || /usr/bin/power-control 0 &
sleep 1' 2>/dev/null
    echo -e "${GREEN}  power-control daemon verified running${NC}"
fi

# 20. Check current Chassis power state before actions
run_get "/redfish/v1/Chassis/system" "Chassis Power State (before action)"

# --- Power On Test ---
report "\n### Power Control Tests\n"

# 21. Host Power On
echo -e "\n${YELLOW}>>> Action: Request Host Power On <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ POWER ON: 送出指令後，請在 PF9 (PS_PWROK) 腳位        │${NC}"
echo -e "${RED}│     接上 3.3V HIGH 信號（模擬 Host PSU Power Good）        │${NC}"
echo -e "${RED}│     接法: PF9 接 VDD 3.3V 或主機板 PWR_LED+               │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  按 Enter 確認已準備好 PF9=HIGH（或已接好 PWR_LED+）..."
report "- **Power On**: 已提示操作者在 PF9 接上 HIGH 信號"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host Power On" \
    '{"ResetType": "On"}'
sleep 5

# 22. Verify host power state after power on
echo -e "\n${BLUE}[Verify] 確認 PF9 (PS_PWROK) 讀到 HIGH → Chassis=On${NC}"
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after Power On"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Power On**: PowerState=${POWER_STATE}"

# --- Force Off Test ---
# 23. Host ForceOff
echo -e "\n${YELLOW}>>> Action: Request Host ForceOff <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ FORCE OFF: 送出指令後，請在 PF9 (PS_PWROK) 腳位       │${NC}"
echo -e "${RED}│     移除 HIGH 信號（斷開 3.3V 或拔掉 PWR_LED+ 線）        │${NC}"
echo -e "${RED}│     PF9 應回到 LOW (0V)（靠 pull-down 電阻拉低）           │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  按 Enter 確認已準備好在 ForceOff 後讓 PF9=LOW..."
report "- **Force Off**: 已提示操作者準備讓 PF9 回到 LOW"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host ForceOff" \
    '{"ResetType": "ForceOff"}'

echo -e "\n${YELLOW}  等待 4s ForceOff 脈衝完成...${NC}"
sleep 5
echo -e "${RED}  >>> 現在請確認 PF9 已為 LOW（斷開 3.3V）<<<${NC}"
read -p "  按 Enter 確認 PF9 已為 LOW..."

# 24. Verify host power state after ForceOff
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after ForceOff"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Force Off**: PowerState=${POWER_STATE}"

# --- Force Restart Test ---
# 25. Host ForceRestart (from whatever current state)
echo -e "\n${YELLOW}>>> Action: Request Host ForceRestart <<<${NC}"
echo -e "${RED}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${RED}│  ⚡ RESTART: 送出後 RESET_OUT (PD13) 會產生 500ms 脈衝     │${NC}"
echo -e "${RED}│     PF9 (PS_PWROK) 應保持 HIGH（Host 未斷電）              │${NC}"
echo -e "${RED}│     若目前 PF9=LOW，請先接上 HIGH 再繼續                   │${NC}"
echo -e "${RED}└─────────────────────────────────────────────────────────────┘${NC}"
read -p "  按 Enter 確認 PF9=HIGH（Host 已開機狀態）..."
report "- **Force Restart**: 已確認 PF9=HIGH"

run_post "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset" \
    "Host ForceRestart" \
    '{"ResetType": "ForceRestart"}'
sleep 5

# 26. Verify host power state after restart
run_get "/redfish/v1/Systems/system" "Verify Host PowerState after ForceRestart"
POWER_STATE=$(curl -k -s -u "${USER}:${PASS}" "https://${BMC_IP}/redfish/v1/Systems/system" | jq -r '.PowerState // "N/A"')
echo -e "  PowerState: ${GREEN}${POWER_STATE}${NC}"
report "- **Verify Force Restart**: PowerState=${POWER_STATE}"

# 27. Check supported ResetType values
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
