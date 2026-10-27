do_install:append:ma35() {
    # Ensure rootfs is mounted rw in fstab for UBIFS persistence and Redfish OTA image staging
    sed -i 's|/dev/root            /                    auto       ro|/dev/root            /                    auto       rw|' ${D}${sysconfdir}/fstab
}
