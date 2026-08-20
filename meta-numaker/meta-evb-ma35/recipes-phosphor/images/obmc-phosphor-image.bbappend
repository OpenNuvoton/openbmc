# OpenBMC image customization for MA35 series
# Both MA35D0 and MA35D05K share the same trimming policy:
# 256MB RAM, 512MB SPI-NAND — no iKVM, no LDAP, no telemetry

# SquashFS with XZ compression for rootfs
EXTRA_IMAGECMD:squashfs-xz:append:ma35d0 = " -b 262144 -Xbcj arm"
EXTRA_IMAGECMD:squashfs-xz:append:ma35d05k = " -b 262144 -Xbcj arm"

IMAGE_FEATURES:remove:ma35d0 = " \
    obmc-ikvm \
    obmc-user-mgmt-ldap \
    obmc-telemetry \
"

IMAGE_FEATURES:remove:ma35d05k = " \
    obmc-ikvm \
    obmc-user-mgmt-ldap \
    obmc-telemetry \
"

IMAGE_INSTALL:remove:ma35d0 = "rest-dbus"

# phosphor-user-manager unconditionally adds new Redfish/D-Bus accounts to the
# "ipmi" supplementary group for privilege mapping. That group is normally
# created by phosphor-ipmi-host (GROUPADD_PARAM), but obmc-host-ipmi/
# obmc-net-ipmi are trimmed from this image, so the group never gets created.
# Without it, useradd fails ("group 'ipmi' does not exist", exit code 6) and
# Redfish AccountService POST/PATCH calls fail with HTTP 500. Create the
# group directly so account management keeps working without pulling in the
# full IPMI host stack.
EXTRA_USERS_PARAMS:append:ma35d0 = " groupadd ipmi;"
EXTRA_USERS_PARAMS:append:ma35d05k = " groupadd ipmi;"
IMAGE_INSTALL:remove:ma35d05k = "rest-dbus"
