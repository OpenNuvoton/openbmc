FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Fix warning: "Group render has never been defined"
# meta-phosphor removes udev from USERADD_PACKAGES which skips render group creation.
# Re-add only the group definition on the udev package.
USERADD_PACKAGES:append = " udev"
GROUPADD_PARAM:udev = "-r render"

SRC_URI += "file://timesyncd-wait-volatile.conf"

do_install:append() {
    install -d ${D}${systemd_system_unitdir}/systemd-timesyncd.service.d
    install -m 0644 ${UNPACKDIR}/timesyncd-wait-volatile.conf ${D}${systemd_system_unitdir}/systemd-timesyncd.service.d/
}

FILES:${PN} += "${systemd_system_unitdir}/systemd-timesyncd.service.d/timesyncd-wait-volatile.conf"
