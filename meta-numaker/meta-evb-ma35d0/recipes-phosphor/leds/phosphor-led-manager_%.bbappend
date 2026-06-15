FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://led-group-config.json"

do_install:append() {
    install -d ${D}${datadir}/phosphor-led-manager
    if [ -f "${WORKDIR}/sources/led-group-config.json" ]; then
        install -m 0644 ${WORKDIR}/sources/led-group-config.json ${D}${datadir}/phosphor-led-manager/
    elif [ -f "${WORKDIR}/led-group-config.json" ]; then
        install -m 0644 ${WORKDIR}/led-group-config.json ${D}${datadir}/phosphor-led-manager/
    else
        install -m 0644 ${UNPACKDIR}/led-group-config.json ${D}${datadir}/phosphor-led-manager/
    fi
}
