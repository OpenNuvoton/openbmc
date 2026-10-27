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
RDEPENDS:${PN}-flash = " \
    phosphor-software-manager-download-mgr \
    phosphor-software-manager-updater \
    phosphor-software-manager-version \
    u-boot-ma35-fw-utils \
    mtd-utils \
"

RDEPENDS:${PN}-flash:append:ma35 = " \
    phosphor-software-manager-updater-ubi \
    mtd-utils-ubifs \
"

RDEPENDS:${PN}-flash:append:df-phosphor-mmc = " \
    phosphor-software-manager-updater-mmc \
"

SUMMARY:${PN}-system = "MA35 System"
RDEPENDS:${PN}-system = " \
    avahi-daemon \
    bmcweb \
    curl \
    entity-manager \
    x86-power-control \
    can-utils \
    iproute2 \
    net-tools \
    ethtool \
    ma35-soc-temp \
    e2fsprogs-resize2fs \
    parted \
"
