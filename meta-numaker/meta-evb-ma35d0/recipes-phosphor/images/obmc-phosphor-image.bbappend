# OpenBMC image customization for MA35D0

# Use SquashFS with XZ compression for rootfs
EXTRA_IMAGECMD:squashfs-xz:append:ma35d0 = " -b 262144 -Xbcj arm"

# MA35D0 has 256MB RAM - we can afford more services than NUC980
# but still trim some heavy features not needed for this BMC
IMAGE_FEATURES:remove:ma35d0 = " \
    obmc-ikvm \
    obmc-user-mgmt-ldap \
    obmc-telemetry \
"

IMAGE_INSTALL:remove:ma35d0 = "rest-dbus"
