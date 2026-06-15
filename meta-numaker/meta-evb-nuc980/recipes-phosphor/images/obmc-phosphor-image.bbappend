# For NUC980 we strip down the default phosphor image to the absolute minimum
# to comfortably run inside a memory-constrained (64MB) and storage-constrained environment.

IMAGE_FEATURES:remove:nuc980 = " \
    obmc-console \
    obmc-debug-collector \
    obmc-fan-control \
    obmc-fan-mgmt \
    obmc-flash-mgmt \
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
"


# Explicitly ensure memory-heavy and non-essential components are ignored
IMAGE_INSTALL:remove:nuc980 = " \
    phosphor-hwmon \
    phosphor-logging \
    phosphor-ipmi-host \
    phosphor-ipmi-net \
    trace-enable \
    webui-vue \
"

