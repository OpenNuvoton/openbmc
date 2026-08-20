SUMMARY = "MA35 Series OpenBMC Package Groups"
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

SUMMARY:${PN}-chassis = "MA35 Chassis"
RDEPENDS:${PN}-chassis = ""

SUMMARY:${PN}-flash = "MA35 Flash"
RDEPENDS:${PN}-flash = ""

SUMMARY:${PN}-system = "MA35 System"
RDEPENDS:${PN}-system = " \
    avahi-daemon \
    bmcweb \
    entity-manager \
    x86-power-control \
    can-utils \
    iproute2 \
    net-tools \
    ethtool \
    ma35-soc-temp \
"
