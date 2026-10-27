FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://${MACHINE}.json"

do_install:append() {
    if [ -f "${D}${systemd_system_unitdir}/xyz.openbmc_project.EntityManager.service" ]; then
        sed -i 's/\[Unit\]/\[Unit\]\nAfter=local-fs.target var-volatile-configuration.service/g' ${D}${systemd_system_unitdir}/xyz.openbmc_project.EntityManager.service
        sed -i 's#ExecStartPre=/bin/mkdir -p /var/configuration#ExecStartPre=/bin/sh -c "mkdir -p /var/configuration /tmp/overlays 2>/dev/null || true"#g' ${D}${systemd_system_unitdir}/xyz.openbmc_project.EntityManager.service
    fi

    # Remove upstream third-party vendor configs and install only this machine's JSON
    rm -rf ${D}${datadir}/entity-manager/configurations
    install -d ${D}${datadir}/entity-manager/configurations
    if [ -f "${WORKDIR}/sources/${MACHINE}.json" ]; then
        install -m 0644 ${WORKDIR}/sources/${MACHINE}.json ${D}${datadir}/entity-manager/configurations/
    elif [ -f "${WORKDIR}/${MACHINE}.json" ]; then
        install -m 0644 ${WORKDIR}/${MACHINE}.json ${D}${datadir}/entity-manager/configurations/
    else
        install -m 0644 ${UNPACKDIR}/${MACHINE}.json ${D}${datadir}/entity-manager/configurations/
    fi

    # Pre-create empty directory for volatile-binds mountpoint
    install -d ${D}/var/configuration
}

FILES:${PN} += "/var/configuration"
