FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://serial-getty@.service \
"

do_install:append() {
    # Install the full customized serial-getty@.service unit to completely override the default one in /etc/systemd/system/
    install -d ${D}${sysconfdir}/systemd/system/
    if [ -f "${UNPACKDIR}/serial-getty@.service" ]; then
        install -m 0644 ${UNPACKDIR}/serial-getty@.service ${D}${sysconfdir}/systemd/system/serial-getty@.service
    elif [ -f "${WORKDIR}/serial-getty@.service" ]; then
        install -m 0644 ${WORKDIR}/serial-getty@.service ${D}${sysconfdir}/systemd/system/serial-getty@.service
    fi
}

FILES:${PN} += " \
    ${sysconfdir}/systemd/system/serial-getty@.service \
"



