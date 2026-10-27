#!/bin/bash
#
# Automated Integration Test: Redfish Firmware Update Pipeline
# Uploads OTA package via multipart/octet-stream, monitors task progress, and validates activation.
#
# NOTE: Run this script on the Host Linux PC (NOT on the BMC).
#

DEFAULT_HOSTNAME="numaker-iot-ma35d05ki1.local"

# Flexible argument parsing:
# Format A: ./test-redfish-update.sh <BMC_IP> <IMAGE_FILE> [user:pass] [Immediate|OnReset]
# Format B: ./test-redfish-update.sh <IMAGE_FILE> [user:pass] [Immediate|OnReset] (defaults BMC_IP to DEFAULT_HOSTNAME)
if [ -f "$1" ] && [[ "$1" == *.tar ]]; then
    BMC_IP="${DEFAULT_HOSTNAME}"
    IMAGE_FILE="$1"
    AUTH="${2:-root:0penBmc}"
    APPLY_TIME="${3:-Immediate}"
else
    BMC_IP="${1:-${DEFAULT_HOSTNAME}}"
    IMAGE_FILE="$2"
    AUTH="${3:-root:0penBmc}"
    APPLY_TIME="${4:-Immediate}"
fi

if [ -z "${IMAGE_FILE}" ] || [ ! -f "${IMAGE_FILE}" ]; then
    echo "Usage: $0 [BMC_IP] <IMAGE_FILE.tar> [user:pass] [Immediate|OnReset]" >&2
    exit 1
fi

echo "=========================================================="
echo " Starting MA35 Redfish OTA Update Verification"
echo " (Running on Host Linux PC, targeting remote BMC)"
echo " BMC Target  : https://${BMC_IP}"
echo " Image File  : ${IMAGE_FILE} ($(du -h "${IMAGE_FILE}" | cut -f1))"
echo " Apply Policy: ${APPLY_TIME}"
echo "=========================================================="

echo ""
echo "[STEP 1] Uploading firmware image package via Redfish..."
printf "  -> Verifying Redfish availability on https://${BMC_IP}..."
PRE_CHECK=false
for i in $(seq 1 15); do
    CODE=$(curl -k -s -o /dev/null -w "%{http_code}" --connect-timeout 2 -u "${AUTH}" "https://${BMC_IP}/redfish/v1/UpdateService" 2>/dev/null || true)
    if [ "${CODE}" = "200" ]; then
        PRE_CHECK=true
        echo " Ready."
        break
    fi
    printf "."
    sleep 2
done

if [ "${PRE_CHECK}" != "true" ]; then
    echo ""
    echo "  [FAIL] Cannot connect to Redfish on https://${BMC_IP} (HTTP ${CODE:-timeout})." >&2
    exit 1
fi

HEADER_OUT=$(mktemp)
BODY_OUT=$(mktemp)

curl -k -s --http1.1 -u "${AUTH}" -D "${HEADER_OUT}" -o "${BODY_OUT}" \
    -X POST \
    -H "Content-Type: application/octet-stream" \
    -H "Expect:" \
    -T "${IMAGE_FILE}" \
    "https://${BMC_IP}/redfish/v1/UpdateService/update"

HTTP_CODE=$(grep -i "^HTTP" "${HEADER_OUT}" | tail -n1 | awk '{print $2}')
TASK_URI=$(grep -i "^Location:" "${HEADER_OUT}" | head -n1 | awk '{print $2}' | tr -d '\r')

if [ -z "${TASK_URI}" ]; then
    TASK_URI=$(cat "${BODY_OUT}" | grep -o '"@odata.id": *"[^"]*"' | head -n1 | cut -d'"' -f4)
fi

rm -f "${HEADER_OUT}" "${BODY_OUT}"

if [ "${HTTP_CODE}" != "200" ] && [ "${HTTP_CODE}" != "202" ]; then
    echo "  [FAIL] Image upload rejected by BMC (HTTP ${HTTP_CODE})." >&2
    exit 1
fi

echo "  [PASS] Image accepted (HTTP ${HTTP_CODE}). Task URI: ${TASK_URI}"

# Step 2: Poll Asynchronous Task Progress
echo ""
echo "[STEP 2] Monitoring update progress..."
TIMEOUT=300
ELAPSED=0
REBOOT_DETECTED=false
LAST_PERCENT=0
EMPTY_POLL_COUNT=0

while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
    TASK_INFO=$(curl -k -s -u "${AUTH}" "https://${BMC_IP}${TASK_URI}" 2>/dev/null || true)
    STATE=$(echo "${TASK_INFO}" | grep -o '"TaskState": *"[^"]*"' | cut -d'"' -f4)
    PERCENT=$(echo "${TASK_INFO}" | grep -o '"PercentComplete": *[0-9]*' | awk '{print $2}')

    if [ "${STATE}" = "Completed" ]; then
        echo "  -> Task State: Completed | Progress: 100% (Elapsed: ${ELAPSED}s)"
        echo "  [SUCCESS] Firmware update completed successfully!"
        break
    elif [ "${STATE}" = "Exception" ] || [ "${STATE}" = "Cancelled" ]; then
        echo "  [FAIL] Firmware update failed with state: ${STATE}" >&2
        echo "${TASK_INFO}" >&2
        exit 1
    fi

    if [ -z "${TASK_INFO}" ]; then
        EMPTY_POLL_COUNT=$((EMPTY_POLL_COUNT + 1))
        if [ "${LAST_PERCENT}" -ge 80 ]; then
            echo "  -> BMC reboot detected following successful firmware flashing!"
            REBOOT_DETECTED=true
            break
        elif [ ${EMPTY_POLL_COUNT} -ge 10 ]; then
            if ! ping -c 1 -W 1 "${BMC_IP}" >/dev/null 2>&1; then
                echo "  -> BMC unreachable (reboot in progress)..."
                REBOOT_DETECTED=true
                break
            else
                echo "  [FAIL] BMC task query timed out after ${EMPTY_POLL_COUNT}s at ${LAST_PERCENT}%." >&2
                exit 1
            fi
        else
            echo "  -> Task query busy (attempt ${EMPTY_POLL_COUNT}/10)... (Elapsed: ${ELAPSED}s)"
            sleep 1
            ELAPSED=$((ELAPSED + 1))
            continue
        fi
    else
        EMPTY_POLL_COUNT=0
    fi

    if echo "${TASK_INFO}" | grep -q 'ResourceNotFound\|404 Not Found'; then
        if [ "${LAST_PERCENT}" -ge 80 ]; then
            echo "  -> Task completed and cleaned up; BMC reboot in progress!"
            REBOOT_DETECTED=true
            break
        else
            echo "  [FAIL] Firmware update task terminated prematurely on BMC (HTTP 404 at ${LAST_PERCENT}%)." >&2
            exit 1
        fi
    fi

    if [ -n "${PERCENT}" ]; then
        LAST_PERCENT="${PERCENT}"
        if [ "${PERCENT}" -eq 0 ]; then
            STAGE_MSG="[Extracting archive on flash...]"
        elif [ "${PERCENT}" -lt 50 ]; then
            STAGE_MSG="[Validating & staging UBI volumes...]"
        elif [ "${PERCENT}" -lt 90 ]; then
            STAGE_MSG="[Writing candidate partitions & bootloader...]"
        else
            STAGE_MSG="[Updating bootpointer & finalizing activation...]"
        fi
        echo "  -> Task State: ${STATE:-Running} | Progress: ${PERCENT}% ${STAGE_MSG} (Elapsed: ${ELAPSED}s)"
    else
        echo "  -> Waiting for BMC task updates... (Elapsed: ${ELAPSED}s)"
    fi

    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ "${STATE}" != "Completed" ] && [ "${REBOOT_DETECTED}" != "true" ]; then
    echo "  [FAIL] Timed out waiting for update task completion." >&2
    exit 1
fi

# Step 3: Wait for BMC to reboot and verify online status and active version
if [ "${REBOOT_DETECTED}" = "true" ] || [ "${APPLY_TIME}" = "Immediate" ]; then
    echo ""
    echo "[STEP 3] Waiting for BMC to complete reboot and become available..."
    REBOOT_TIMEOUT=180
    REBOOT_ELAPSED=0
    BMC_READY=false

    # Give BMC time to cycle services and initiate hardware reset
    echo "  -> Waiting for BMC to shut down and reboot..."
    sleep 15
    while [ ${REBOOT_ELAPSED} -lt ${REBOOT_TIMEOUT} ]; do
        HTTP_CHECK=$(curl -k -s -o /dev/null -w "%{http_code}" -u "${AUTH}" "https://${BMC_IP}/redfish/v1/Managers/bmc" 2>/dev/null || true)
        if [ "${HTTP_CHECK}" = "200" ]; then
            BMC_READY=true
            echo ""
            echo "  [PASS] BMC is back online (${BMC_IP}, HTTP ${HTTP_CHECK}) after ${REBOOT_ELAPSED}s."
            break
        fi

        # If the target IP does not respond after 15s, detect if DHCP reassigned a new IP via mDNS
        if [ ${REBOOT_ELAPSED} -ge 15 ]; then
            DETECTED_IP=$(avahi-resolve-host-name -4 "${DEFAULT_HOSTNAME}" 2>/dev/null | awk '{print $2}')
            if [ -n "${DETECTED_IP}" ] && [ "${DETECTED_IP}" != "${BMC_IP}" ]; then
                echo ""
                echo "  -> Notice: Detected DHCP IP reassignment (${BMC_IP} -> ${DETECTED_IP} via ${DEFAULT_HOSTNAME})."
                BMC_IP="${DETECTED_IP}"
            fi
        fi

        printf "\r  -> Waiting for BMC services to come online... (%ds / %ds)" "${REBOOT_ELAPSED}" "${REBOOT_TIMEOUT}"
        sleep 2
        REBOOT_ELAPSED=$((REBOOT_ELAPSED + 2))
    done
    echo ""

    if [ "${BMC_READY}" != "true" ]; then
        echo "  [FAIL] BMC failed to respond after reboot within ${REBOOT_TIMEOUT}s." >&2
        exit 1
    fi

    echo ""
    echo "[STEP 4] Verifying active firmware inventory..."
    FW_INV=$(curl -k -s -u "${AUTH}" "https://${BMC_IP}/redfish/v1/UpdateService/FirmwareInventory" | grep -o '"@odata.id": *"[^"]*"' || true)
    echo "  ${FW_INV}"

    SSH_USER="${AUTH%%:*}"
    SSH_PASS="${AUTH#*:}"
    if command -v sshpass >/dev/null 2>&1 && [ -n "${SSH_PASS}" ]; then
        echo ""
        echo "[STEP 5] Verifying active storage bank & kernel cmdline via SSH..."
        sshpass -p "${SSH_PASS}" ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ConnectTimeout=5 "${SSH_USER}@${BMC_IP}" \
            "echo -n '  Active bootside : '; fw_printenv bootside 2>/dev/null || echo 'N/A'; echo -n '  Kernel root dev : '; grep -o 'root=[^ ]*' /proc/cmdline 2>/dev/null || echo 'N/A'" 2>/dev/null || true
    fi
fi

echo ""
echo "=========================================================="
echo " Redfish Firmware Update Verification Completed."
echo "=========================================================="
