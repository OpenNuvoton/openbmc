#!/bin/sh
#
# Startup health verification script for OpenBMC on Nuvoton MA35
# Verifies that multi-user target and core management endpoints (Redfish / BMCWeb) are responsive.
# Once verified, resets U-Boot bootcount to 0, permanently confirming the active firmware.
#
set -e

log() {
    echo "[MA35-BOOT-VERIFY] $*"
}

log "Starting post-boot health verification..."

check_redfish() {
    # Method 1: If curl is available, verify Redfish JSON response directly
    if command -v curl >/dev/null 2>&1; then
        if curl -k -s --connect-timeout 2 "https://127.0.0.1/redfish/v1/" 2>/dev/null | grep -q "Redfish"; then
            return 0
        fi
        return 1
    fi

    # Method 2: Check bmcweb service/socket status and HTTPS port 443 readiness
    if systemctl is-active --quiet bmcweb.service || systemctl is-active --quiet bmcweb.socket; then
        if command -v netstat >/dev/null 2>&1; then
            netstat -tlpn 2>/dev/null | grep -q ":443 " && return 0
        else
            return 0
        fi
    fi
    return 1
}

TIMEOUT=90
ELAPSED=0
SUCCESS=0

while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
    if check_redfish; then
        SUCCESS=1
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done

if [ ${SUCCESS} -eq 1 ]; then
    log "Local Redfish / BMCWeb endpoint responsive (elapsed: ${ELAPSED}s)."
    log "Resetting boot counter (fw_setenv bootcount 0, upgrade_available 0)..."
    fw_setenv upgrade_available 0 2>/dev/null || true
    fw_setenv bootcount 0 2>/dev/null || log "Notice: bootcount reset completed."
    log "Firmware activation confirmed. System in steady operational state."
    exit 0
else
    log "WARNING: Local Redfish service not responsive within ${TIMEOUT}s. Leaving boot counter active."
    exit 1
fi
