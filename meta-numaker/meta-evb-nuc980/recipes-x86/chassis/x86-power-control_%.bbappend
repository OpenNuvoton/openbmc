FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI:append:numaker-iot-nuc980g2 = " file://power-config-host0.json"

do_install:append:numaker-iot-nuc980g2() {
    install -m 0755 -d ${D}/${datadir}/${BPN}
    install -m 0644 -D ${UNPACKDIR}/power-config-host0.json \
                   ${D}/${datadir}/${BPN}/
}
