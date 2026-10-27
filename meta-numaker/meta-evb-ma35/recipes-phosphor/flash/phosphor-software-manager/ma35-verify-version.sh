#!/bin/sh
#
# Nuvoton MA35 OpenBMC Firmware Version & Anti-Rollback Verification Script
# Validates candidate image MANIFEST against machine model and hardware security baseline.
#
set -e

MANIFEST_FILE="$1"

if [ -z "${MANIFEST_FILE}" ]; then
    echo "Usage: $0 <path_to_MANIFEST | path_to_image_dir>" >&2
    exit 1
fi

if [ -d "${MANIFEST_FILE}" ]; then
    MANIFEST_FILE="${MANIFEST_FILE}/MANIFEST"
fi

if [ ! -f "${MANIFEST_FILE}" ]; then
    echo "ERROR: MANIFEST file not found at '${MANIFEST_FILE}'" >&2
    exit 1
fi

# Parse MANIFEST key-value pairs
parse_manifest_key() {
    local key="$1"
    grep "^${key}=" "${MANIFEST_FILE}" | head -n1 | cut -d'=' -f2- | tr -d '\r'
}

CANDIDATE_MACHINE=$(parse_manifest_key "MachineName")
CANDIDATE_VERSION=$(parse_manifest_key "version")
CANDIDATE_SEC_VER=$(parse_manifest_key "SecurityVersion")
CANDIDATE_PURPOSE=$(parse_manifest_key "purpose")

# Detect current machine model from /etc/os-release
CURRENT_MACHINE=""
if [ -f /etc/os-release ]; then
    CURRENT_MACHINE=$(grep -E "^(OPENBMC_TARGET_MACHINE|MACHINE)=" /etc/os-release | head -n1 | cut -d'=' -f2- | tr -d '"\r')
fi
if [ -z "${CURRENT_MACHINE}" ] && [ -f /etc/machine-info ]; then
    CURRENT_MACHINE=$(grep "^CHASSIS=" /etc/machine-info | cut -d'=' -f2- | tr -d '"\r')
fi

# 1. Machine Model Compatibility Check
if [ -n "${CURRENT_MACHINE}" ] && [ -n "${CANDIDATE_MACHINE}" ]; then
    if [ "${CURRENT_MACHINE}" != "${CANDIDATE_MACHINE}" ]; then
        echo "ERROR [MA35-VERIFY]: Machine model mismatch! Candidate targets '${CANDIDATE_MACHINE}', but active hardware is '${CURRENT_MACHINE}'." >&2
        exit 1
    fi
    echo "INFO [MA35-VERIFY]: Machine model '${CANDIDATE_MACHINE}' matches active platform."
fi

# 2. Retrieve Active Version and Anti-Rollback Baseline
ACTIVE_VERSION=""
if [ -f /etc/os-release ]; then
    ACTIVE_VERSION=$(grep "^VERSION_ID=" /etc/os-release | cut -d'=' -f2- | tr -d '"\r')
fi

# Anti-rollback baseline from hardware OTP or persistent store (default minimum: 1)
HW_ANTI_ROLLBACK=1
if [ -f /sys/firmware/ma35/anti_rollback ]; then
    HW_ANTI_ROLLBACK=$(cat /sys/firmware/ma35/anti_rollback)
elif [ -f /var/persist/ma35_anti_rollback ]; then
    HW_ANTI_ROLLBACK=$(cat /var/persist/ma35_anti_rollback)
fi

# 3. Anti-Rollback & Identical Version Check
[ -z "${CANDIDATE_SEC_VER}" ] && CANDIDATE_SEC_VER=1

if [ "${CANDIDATE_SEC_VER}" -lt "${HW_ANTI_ROLLBACK}" ]; then
    echo "ERROR [MA35-VERIFY]: Firmware rollback prohibited! Candidate SecurityVersion (${CANDIDATE_SEC_VER}) is below hardware anti-rollback baseline (${HW_ANTI_ROLLBACK})." >&2
    exit 1
fi

if [ -n "${ACTIVE_VERSION}" ] && [ "${CANDIDATE_VERSION}" = "${ACTIVE_VERSION}" ]; then
    echo "INFO [MA35-VERIFY]: Candidate version matches active version '${ACTIVE_VERSION}'. Allowed for repair / re-flashing."
else
    echo "INFO [MA35-VERIFY]: Candidate version '${CANDIDATE_VERSION}' (SecurityVersion=${CANDIDATE_SEC_VER}) passed anti-rollback checks."
fi

exit 0
