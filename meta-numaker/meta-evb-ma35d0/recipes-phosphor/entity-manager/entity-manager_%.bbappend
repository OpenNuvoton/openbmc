FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://numaker-iot-ma35d0.json"

do_install:append() {
    install -d ${D}${datadir}/entity-manager/configurations
    if [ -f "${WORKDIR}/sources/numaker-iot-ma35d0.json" ]; then
        install -m 0644 ${WORKDIR}/sources/numaker-iot-ma35d0.json ${D}${datadir}/entity-manager/configurations/
    else
        install -m 0644 ${WORKDIR}/numaker-iot-ma35d0.json ${D}${datadir}/entity-manager/configurations/
    fi
}
