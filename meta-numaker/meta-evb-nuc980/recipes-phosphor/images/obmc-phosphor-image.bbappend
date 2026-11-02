# For NUC980 we strip down the default phosphor image to the absolute minimum
# to comfortably run inside a memory-constrained (128MB) and storage-constrained environment.

IMAGE_FEATURES:remove:nuc980 = " \
    obmc-console \
    obmc-debug-collector \
    obmc-devtools \
    obmc-dbus-monitor \
    obmc-fan-control \
    obmc-fan-mgmt \
    obmc-flash-mgmt \
    obmc-health-monitor \
    obmc-host-ctl \
    obmc-host-ipmi \
    obmc-ikvm \
    obmc-inventories \
    obmc-logging-mgmt \
    obmc-sensors \
    obmc-software \
    obmc-system-mgmt \
    obmc-telemetry \
    obmc-user-mgmt-ldap \
    obmc-webui \
    ssh-server-openssh \
"


# Explicitly ensure memory-heavy and non-essential components are ignored
IMAGE_INSTALL:remove:nuc980 = " \
    phosphor-certificate-manager \
    phosphor-hwmon \
    phosphor-logging \
    phosphor-ipmi-host \
    phosphor-ipmi-net \
    phosphor-dbus-monitor \
    obmc-phosphor-power \
    trace-enable \
    webui-vue \
"

# phosphor-user-manager unconditionally adds new Redfish/D-Bus accounts to the
# "ipmi" supplementary group for privilege mapping. That group is normally
# created by phosphor-ipmi-host (GROUPADD_PARAM), but obmc-host-ipmi/
# obmc-net-ipmi are trimmed from this image, so the group never gets created.
# Without it, useradd fails ("group 'ipmi' does not exist", exit code 6) and
# Redfish AccountService POST/PATCH calls fail with HTTP 500. Create the
# group directly so account management keeps working without pulling in the
# full IPMI host stack.
EXTRA_USERS_PARAMS:append:nuc980 = " groupadd ipmi;"


