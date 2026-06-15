# Add system-wide DefaultTimeoutStartSec and disable core dumps to prevent CPU/IO lockups
do_install:append() {
    if [ -f "${D}${systemd_unitdir}/system.conf.d/service-restart-policy.conf" ]; then
        echo "DefaultTimeoutStartSec=300s" >> ${D}${systemd_unitdir}/system.conf.d/service-restart-policy.conf
        echo "DefaultLimitCORE=0" >> ${D}${systemd_unitdir}/system.conf.d/service-restart-policy.conf
    fi

    # Disable readahead on MTD block devices to reduce unnecessary I/O
    install -d ${D}${nonarch_base_libdir}/udev/rules.d
    echo 'ACTION=="add|change", KERNEL=="mtdblock*", ATTR{queue/read_ahead_kb}="0"' \
        > ${D}${nonarch_base_libdir}/udev/rules.d/60-mtd-readahead.rules
}

FILES:${PN} += "${nonarch_base_libdir}/udev/rules.d"
