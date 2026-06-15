SUMMARY = "MA35D0 OpenBMC Package Groups"
PR = "r1"

inherit packagegroup

PROVIDES = "${PACKAGES}"
PACKAGES = " \
    ${PN} \
    ${PN}-chassis \
    ${PN}-flash \
    ${PN}-system \
"

RDEPENDS:${PN} = " \
    ${PN}-chassis \
    ${PN}-flash \
    ${PN}-system \
"

PROVIDES += "virtual/obmc-chassis-mgmt"
PROVIDES += "virtual/obmc-flash-mgmt"
PROVIDES += "virtual/obmc-system-mgmt"

RPROVIDES:${PN}-chassis += "virtual-obmc-chassis-mgmt"
RPROVIDES:${PN}-flash += "virtual-obmc-flash-mgmt"
RPROVIDES:${PN}-system += "virtual-obmc-system-mgmt"

SUMMARY:${PN}-chassis = "MA35D0 Chassis"
RDEPENDS:${PN}-chassis = ""

SUMMARY:${PN}-flash = "MA35D0 Flash"
RDEPENDS:${PN}-flash = ""

SUMMARY:${PN}-system = "MA35D0 System"
RDEPENDS:${PN}-system = " \
    bmcweb \
    entity-manager \
"
