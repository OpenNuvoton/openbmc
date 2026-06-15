FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-Simplify-system-LED-LocationIndicatorActive.patch \
"

# Minimal set for NUC980 (64MB)
# Disable non-Redfish features to save space

EXTRA_OEMESON:append:nuc980 = " \
    -Dkvm=disabled \
    -Dvm-websocket=disabled \
    -Dredfish-dump-log=disabled \
    -Dredfish-dbus-log=enabled \
    -Drest=disabled \
"

do_install:append:nuc980() {
    if [ -f ${D}${systemd_system_unitdir}/bmcweb.service ]; then
        # Change absolute StateDirectory=/home/root to relative StateDirectory=bmcweb
        # to prevent systemd warnings and enable writing bmcweb_persistent_data.json
        # into the writable /var/lib/bmcweb/ directory.
        sed -i 's|^StateDirectory=.*|StateDirectory=bmcweb|' ${D}${systemd_system_unitdir}/bmcweb.service
        # Increase WatchdogSec to 600s to avoid watchdog timeout coredumps under heavy SSL load
        sed -i 's|^WatchdogSec=.*|WatchdogSec=600s|' ${D}${systemd_system_unitdir}/bmcweb.service
        # Serialize: start bmcweb AFTER entity-manager to avoid concurrent SquashFS I/O storm
        # This lets shared libraries get page-cached by earlier services first
        sed -i '/^\[Unit\]/a After=xyz.openbmc_project.EntityManager.service' ${D}${systemd_system_unitdir}/bmcweb.service
    fi
}



