FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://nuc980-evb.json \
            file://0001-Add-Chassis-LED-association-support.patch \
"

# Force EntityManager to start after local-fs.target and var-volatile-configuration.service to ensure /var/configuration is writable
do_install:append() {
    if [ -f "${D}${systemd_system_unitdir}/xyz.openbmc_project.EntityManager.service" ]; then
        sed -i 's/\[Unit\]/\[Unit\]\nAfter=local-fs.target var-volatile-configuration.service/g' ${D}${systemd_system_unitdir}/xyz.openbmc_project.EntityManager.service
    fi
    install -d ${D}${datadir}/entity-manager/configurations
    if [ -f "${WORKDIR}/sources/nuc980-evb.json" ]; then
        install -m 0644 ${WORKDIR}/sources/nuc980-evb.json ${D}${datadir}/entity-manager/configurations/
    else
        install -m 0644 ${WORKDIR}/nuc980-evb.json ${D}${datadir}/entity-manager/configurations/
    fi

    # Pre-create empty directory for volatile-binds mountpoint
    install -d ${D}/var/configuration
}

FILES:${PN} += "/var/configuration"


