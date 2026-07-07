FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI:append:numaker-iot-ma35d0 = " file://power-config-host0.json"
SRC_URI:append:numaker-iot-ma35d05ki1 = " file://power-config-host0.json"

do_install:append:numaker-iot-ma35d0() {
    install -m 0755 -d ${D}/${datadir}/${BPN}
    install -m 0644 -D ${UNPACKDIR}/power-config-host0.json \
                   ${D}/${datadir}/${BPN}/
}

do_install:append:numaker-iot-ma35d05ki1() {
    install -m 0755 -d ${D}/${datadir}/${BPN}
    install -m 0644 -D ${UNPACKDIR}/power-config-host0.json \
                   ${D}/${datadir}/${BPN}/
}
