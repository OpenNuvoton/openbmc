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

# MA35 boards have no dedicated "bmc booted" heartbeat LED (numaker-iot-ma35d0
# only wires "front_id"/"power", numaker-iot-ma35d05ki1 only wires "front_id"),
# so led-group-config.json intentionally does not define a "bmc_booted" group.
# The base recipe unconditionally enables obmc-led-group-start@bmc_booted.service
# via multi-user.target.wants, which then fails at boot with "Unknown object"
# because the corresponding D-Bus LED group was never created. Disable that
# unit for this platform instead of asserting a non-existent LED group.
SYSTEMD_LINK:${PN}:remove = "../obmc-led-group-start@.service:multi-user.target.wants/obmc-led-group-start@bmc_booted.service"
SYSTEMD_OVERRIDE:${PN}:remove = "bmc_booted.conf:obmc-led-group-start@bmc_booted.service.d/bmc_booted.conf"
