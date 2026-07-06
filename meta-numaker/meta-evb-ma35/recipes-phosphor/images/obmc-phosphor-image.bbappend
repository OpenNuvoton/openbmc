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
IMAGE_INSTALL:remove:ma35d05k = "rest-dbus"
