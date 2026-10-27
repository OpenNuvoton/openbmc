#!/bin/bash
#
# Automated Validation Test: Redfish Firmware Inventory & Anti-Rollback Guard
# Tests candidate package verification against MA35 IBR anti-rollback baseline and machine model.
#
# NOTE: Run this script on the Host Linux PC (NOT on the BMC).
#

BMC_IP="${1:-numaker-iot-ma35d05ki1.local}"
AUTH="${2:-root:0penBmc}"
TARGET_MACHINE="numaker-iot-ma35d05ki1"
TMP_DIR=$(mktemp -d /tmp/ma35-fw-test-XXXXXX)

cleanup() {
    rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

echo "=========================================================="
echo " Starting MA35 Redfish Anti-Rollback & Machine Guard Tests"
echo " (Running on Host Linux PC, targeting remote BMC)"
echo " Target BMC  : https://${BMC_IP}"
echo "=========================================================="

# Test 1: Query Firmware Inventory
echo ""
echo "[TEST 1] Querying Redfish Firmware Inventory..."
INVENTORY_RESP=$(curl -k -s -u "${AUTH}" "https://${BMC_IP}/redfish/v1/UpdateService/FirmwareInventory")
if [ $? -eq 0 ] && echo "${INVENTORY_RESP}" | grep -q "Members"; then
    echo "  [PASS] FirmwareInventory endpoint is accessible and returned members list."
else
    echo "  [FAIL] Unable to retrieve FirmwareInventory from BMC."
    exit 1
fi

# Helper function: Upload package and verify rejection
# OpenBMC Redfish UpdateService accepts image uploads via HTTP POST (returning HTTP 202 Accepted)
# and processes verification asynchronously, failing the task with TaskState: Exception if invalid.
upload_and_check_rejection() {
    local tar_file="$1"
    local desc="$2"
    local headers_file="${TMP_DIR}/headers.txt"

    local http_out
    http_out=$(curl -k -s -D "${headers_file}" -u "${AUTH}" -X POST \
        -H "Content-Type: application/octet-stream" \
        -H "Expect:" \
        -T "${tar_file}" \
        "https://${BMC_IP}/redfish/v1/UpdateService/update")

    local http_code
    http_code=$(awk '/^HTTP\// {print $2}' "${headers_file}" | tail -n1)

    # Direct synchronous rejection
    if [ "${http_code}" = "400" ] || [ "${http_code}" = "422" ]; then
        echo "  [PASS] Correctly rejected by BMC (HTTP ${http_code})."
        return 0
    fi

    # Asynchronous task evaluation (HTTP 202 Accepted)
    if [ "${http_code}" = "202" ]; then
        local task_url
        task_url=$(grep -i "^location:" "${headers_file}" | tr -d '\r\n' | awk '{print $2}')
        local task_id
        task_id=$(echo "${task_url}" | grep -oE '[0-9]+$')
        if [ -z "${task_id}" ]; then
            task_id=$(echo "${http_out}" | grep -oE '"Id": *"[0-9]+"' | grep -oE '[0-9]+' | head -n1)
        fi

        if [ -n "${task_id}" ]; then
            local task_state=""
            local task_msg=""
            for _ in $(seq 1 10); do
                local task_json
                task_json=$(curl -k -s -u "${AUTH}" "https://${BMC_IP}/redfish/v1/TaskService/Tasks/${task_id}")
                task_state=$(echo "${task_json}" | grep -o '"TaskState": *"[^"]*"' | head -n1 | cut -d'"' -f4)
                if [ "${task_state}" = "Exception" ] || [ "${task_state}" = "Completed" ] || [ "${task_state}" = "Cancelled" ]; then
                    task_msg=$(echo "${task_json}" | grep -o '"MessageId": *"[^"]*"' | tail -n1 | cut -d'"' -f4)
                    break
                fi
                sleep 1
            done

            if [ "${task_state}" = "Exception" ]; then
                echo "  [PASS] Candidate package was correctly rejected by verification guard (TaskState: Exception, ${task_msg:-TaskAborted})."
                return 0
            elif [ "${task_state}" = "Completed" ]; then
                echo "  [FAIL] Incompatible package was unexpectedly accepted and completed by BMC!"
                return 1
            else
                echo "  [WARN/FAIL] Task finished with state: ${task_state:-Timeout}."
                return 1
            fi
        else
            echo "  [WARN] HTTP 202 received but unable to parse Task ID from response."
            return 1
        fi
    fi

    echo "  [WARN/FAIL] Expected HTTP 400 or HTTP 202 (with Task Exception), got HTTP ${http_code}."
    return 1
}

# Test 2: Mismatched Machine Model Rejection
echo ""
echo "[TEST 2] Testing rejection of mismatched MachineName..."
mkdir -p "${TMP_DIR}/mismatch"
cat <<EOF > "${TMP_DIR}/mismatch/MANIFEST"
purpose=xyz.openbmc_project.Software.Version.VersionPurpose.BMC
version=9.99.0-incompatible
MachineName=unsupported-machine-target
CompatibleName=unsupported-machine-target
SecurityVersion=99
ExtendedVersion=OpenBMC MA35 Series Secure OTA
EOF
echo "DUMMY_KERNEL" > "${TMP_DIR}/mismatch/image-kernel"
echo "DUMMY_ROFS" > "${TMP_DIR}/mismatch/image-rofs"
echo "DUMMY_RWFS" > "${TMP_DIR}/mismatch/image-rwfs"
echo "DUMMY_UBOOT" > "${TMP_DIR}/mismatch/image-u-boot"
tar -C "${TMP_DIR}/mismatch" -cf "${TMP_DIR}/mismatch.tar" MANIFEST image-kernel image-rofs image-rwfs image-u-boot
upload_and_check_rejection "${TMP_DIR}/mismatch.tar" "mismatched MachineName"

# Test 3: Version Downgrade / Anti-Rollback Violation Rejection
echo ""
echo "[TEST 3] Testing rejection of version below anti-rollback threshold..."
mkdir -p "${TMP_DIR}/rollback"
cat <<EOF > "${TMP_DIR}/rollback/MANIFEST"
purpose=xyz.openbmc_project.Software.Version.VersionPurpose.BMC
version=1.0.0-legacy
MachineName=${TARGET_MACHINE}
CompatibleName=${TARGET_MACHINE}
SecurityVersion=0
ExtendedVersion=OpenBMC MA35 Series Secure OTA
EOF
echo "DUMMY_KERNEL" > "${TMP_DIR}/rollback/image-kernel"
echo "DUMMY_ROFS" > "${TMP_DIR}/rollback/image-rofs"
echo "DUMMY_RWFS" > "${TMP_DIR}/rollback/image-rwfs"
echo "DUMMY_UBOOT" > "${TMP_DIR}/rollback/image-u-boot"
tar -C "${TMP_DIR}/rollback" -cf "${TMP_DIR}/rollback.tar" MANIFEST image-kernel image-rofs image-rwfs image-u-boot
upload_and_check_rejection "${TMP_DIR}/rollback.tar" "SecurityVersion=0 rollback violation"

echo ""
echo "=========================================================="
echo " All Anti-Rollback & Machine Guard Tests Completed."
echo "=========================================================="
