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
    phosphor-user-manager \
    phosphor-dbus-monitor \
    obmc-phosphor-power \
    trace-enable \
    webui-vue \
"

