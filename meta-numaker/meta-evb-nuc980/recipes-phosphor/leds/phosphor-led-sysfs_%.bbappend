FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

do_install:append() {
    # Create systemd D-Bus activation symlink to map dbus-broker activation to the real service
    install -d ${D}${sysconfdir}/systemd/system
    ln -sf ${systemd_system_unitdir}/phosphor-ledcontroller.service \
        ${D}${sysconfdir}/systemd/system/dbus-xyz.openbmc_project.LED.Controller.service
}

# Package the symlink
FILES:${PN} += "${sysconfdir}/systemd/system/dbus-xyz.openbmc_project.LED.Controller.service"
