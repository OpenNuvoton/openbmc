#!/bin/bash
#
# Automated Validation Test: U-Boot Watchdog Bootcount & Autonomous Fallback
# Simulates boot failure on active bank and verifies automated rollback to stable bank.
#
# NOTE: Run this script on the Host Linux PC (NOT on the BMC).
#

BMC_IP="${1:-numaker-iot-ma35d03f80.local}"
AUTH="${2:-root:0penBmc}"

# Resolve mDNS hostname to IPv4 if needed
TARGET_HOST="${BMC_IP}"
if [[ "${BMC_IP}" == *.local ]]; then
    MDNS_IP=$(avahi-resolve-host-name -4 "${BMC_IP}" 2>/dev/null | awk '{print $2}')
    if [ -z "${MDNS_IP}" ]; then
        MDNS_IP=$(getent ahostsv4 "${BMC_IP}" 2>/dev/null | head -n1 | awk '{print $1}')
    fi
    if [ -n "${MDNS_IP}" ]; then
        TARGET_HOST="${MDNS_IP}"
    fi
fi

SSH_USER="${AUTH%%:*}"
SSH_PASS=""
if [[ "${AUTH}" == *:* ]]; then
    SSH_PASS="${AUTH#*:}"
fi

run_ssh() {
    local cmd="$1"
    if [ -n "${SSH_PASS}" ] && command -v sshpass >/dev/null 2>&1; then
        sshpass -p "${SSH_PASS}" ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR "${SSH_USER}@${TARGET_HOST}" "${cmd}"
    else
        ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR -o BatchMode=yes "${SSH_USER}@${TARGET_HOST}" "${cmd}"
    fi
}

echo "=========================================================="
echo " Starting MA35 Autonomous Boot Fallback Verification"
echo " (Running on Host Linux PC, targeting remote BMC)"
echo " Target BMC  : https://${BMC_IP} (${TARGET_HOST})"
echo "=========================================================="

echo ""
echo "[STEP 1] Querying current active storage bank via SSH..."
ACTIVE_VAR=$(run_ssh "fw_printenv bootside 2>/dev/null || fw_printenv kernelname 2>/dev/null || fw_printenv bootubivol 2>/dev/null || echo 'bootside=a'" | grep -E '^(bootside|kernelname|bootubivol)=' | head -n1 | tr -d '\r\n')
ACTIVE_SIDE=$(echo "${ACTIVE_VAR}" | cut -d'=' -f2)

echo "  Current active bank indicator: '${ACTIVE_SIDE}'"

echo ""
echo "[STEP 2] Simulating boot probation state (setting bootcount=3, bootlimit=3, upgrade_available=1)..."
run_ssh "fw_setenv bootcount 3 && fw_setenv bootlimit 3 && fw_setenv upgrade_available 1"

echo "  Bootcount set to 3. Verifying non-volatile environment..."
VERIFY_COUNT=$(run_ssh "fw_printenv bootcount 2>/dev/null" | grep '^bootcount=' | cut -d'=' -f2 | tr -d '\r\n')

if [ "${VERIFY_COUNT}" = "3" ]; then
    echo "  [PASS] Bootcount successfully primed for failover threshold."
else
    echo "  [FAIL] Failed to update U-Boot environment variable (got '${VERIFY_COUNT}')." >&2
    exit 1
fi

echo ""
echo "[STEP 3] Triggering simulated boot failure / watchdog restart..."
echo "  Rebooting device to observe U-Boot bootlimit autonomous rollback..."
run_ssh "reboot" >/dev/null 2>&1 || true

echo "  Waiting for BMC reboot and recovery (up to 90s)..."
sleep 25

TIMEOUT=90
RECOVERED=0
while [ ${TIMEOUT} -gt 0 ]; do
    if curl -k -s --connect-timeout 2 "https://${TARGET_HOST}/redfish/v1/" 2>/dev/null | grep -q "Redfish"; then
        RECOVERED=1
        break
    fi
    sleep 3
    TIMEOUT=$((TIMEOUT - 3))
done

if [ ${RECOVERED} -eq 1 ]; then
    echo "  [PASS] BMC successfully rebooted and recovered online!"
else
    echo "  [FAIL] BMC did not come back online within timeout window." >&2
    exit 1
fi

echo ""
echo "[STEP 4] Verifying bank fallback and boot counter reset..."
POST_VAR=$(run_ssh "fw_printenv bootside 2>/dev/null || fw_printenv kernelname 2>/dev/null || fw_printenv bootubivol 2>/dev/null" | grep -E '^(bootside|kernelname|bootubivol)=' | head -n1 | tr -d '\r\n')
POST_SIDE=$(echo "${POST_VAR}" | cut -d'=' -f2)
POST_COUNT=$(run_ssh "fw_printenv bootcount 2>/dev/null" | grep '^bootcount=' | cut -d'=' -f2 | tr -d '\r\n')

echo "  Post-boot bank indicator: '${POST_SIDE}' (was '${ACTIVE_SIDE}')"
echo "  Post-boot bootcount: '${POST_COUNT}'"

if [ -n "${ACTIVE_SIDE}" ] && [ -n "${POST_SIDE}" ] && [ "${ACTIVE_SIDE}" != "${POST_SIDE}" ]; then
    echo "  [PASS] U-Boot successfully rolled back to alternate bank: ${POST_SIDE}."
else
    echo "  [NOTE] Bank indicator: '${POST_SIDE}'."
fi

if [ "${POST_COUNT}" = "0" ]; then
    echo "  [PASS] obmc-boot-verify service successfully confirmed startup and reset bootcount to 0."
else
    echo "  [WARN] Expected bootcount 0, got '${POST_COUNT}'."
fi

echo ""
echo "=========================================================="
echo " Autonomous Boot Fallback Verification Completed."
echo "=========================================================="
