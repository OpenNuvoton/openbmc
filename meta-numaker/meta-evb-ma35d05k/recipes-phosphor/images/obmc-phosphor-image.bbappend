# OpenBMC image customization for MA35D0K5

# Use SquashFS with XZ compression for rootfs
EXTRA_IMAGECMD:squashfs-xz:append:ma35d05k = " -b 262144 -Xbcj arm"

IMAGE_FEATURES:remove:ma35d05k = " \
    obmc-ikvm \
    obmc-user-mgmt-ldap \
    obmc-telemetry \
"

IMAGE_INSTALL:remove:ma35d05k = "rest-dbus"
