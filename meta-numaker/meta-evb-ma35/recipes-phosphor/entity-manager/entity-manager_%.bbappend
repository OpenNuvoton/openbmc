FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://${MACHINE}.json"

do_install:append() {
    install -d ${D}${datadir}/entity-manager/configurations
    if [ -f "${WORKDIR}/sources/${MACHINE}.json" ]; then
        install -m 0644 ${WORKDIR}/sources/${MACHINE}.json ${D}${datadir}/entity-manager/configurations/
    elif [ -f "${WORKDIR}/${MACHINE}.json" ]; then
        install -m 0644 ${WORKDIR}/${MACHINE}.json ${D}${datadir}/entity-manager/configurations/
    else
        install -m 0644 ${UNPACKDIR}/${MACHINE}.json ${D}${datadir}/entity-manager/configurations/
    fi
}
