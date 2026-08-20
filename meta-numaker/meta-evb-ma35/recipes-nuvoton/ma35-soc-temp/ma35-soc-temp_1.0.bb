SUMMARY = "MA35 SoC Temperature Sensor D-Bus Service"
DESCRIPTION = "Publishes MA35 internal TSEN temperature sensor to OpenBMC D-Bus for bmcweb and Redfish"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/Apache-2.0;md5=89aea4e17d99a7cacdbeed46a0096b10"

inherit cmake pkgconfig systemd

DEPENDS = "boost sdbusplus systemd"

SRC_URI = " \
    file://CMakeLists.txt \
    file://ma35-soc-temp.cpp \
    file://ma35-soc-temp.service \
"

S = "${UNPACKDIR}"

SYSTEMD_SERVICE:${PN} = "ma35-soc-temp.service"
SYSTEMD_AUTO_ENABLE = "enable"

do_install:append() {
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${UNPACKDIR}/ma35-soc-temp.service ${D}${systemd_system_unitdir}/
}
