FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Fix warning: "Group render has never been defined"
# meta-phosphor removes udev from USERADD_PACKAGES (USERADD_PACKAGES:remove = "udev"),
# which negates any USERADD_PACKAGES:append = " udev" and skips render group creation.
# Add the render group to ${PN} (systemd) instead so groupadd is executed.
GROUPADD_PARAM:${PN} += "-r render;"

# Fix warning: "${rootlibexecdir}/systemd/systemd does not exist"
# meta-phosphor uses ${rootlibexecdir} (/usr/libexec in merged-usr), but
# systemd installs its binary to ${systemd_unitdir}/systemd (/usr/lib/systemd/systemd).
ALTERNATIVE_TARGET[init] = "${systemd_unitdir}/systemd"

SRC_URI += "file://timesyncd-wait-volatile.conf"

do_install:append() {
    install -d ${D}${systemd_system_unitdir}/systemd-timesyncd.service.d
    install -m 0644 ${UNPACKDIR}/timesyncd-wait-volatile.conf ${D}${systemd_system_unitdir}/systemd-timesyncd.service.d/
}

FILES:${PN} += "${systemd_system_unitdir}/systemd-timesyncd.service.d/timesyncd-wait-volatile.conf"
