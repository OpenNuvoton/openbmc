SUMMARY = "Trusted Firmware-A for Nuvoton MA35D0"
LICENSE = "BSD-3-Clause"
LIC_FILES_CHKSUM = "file://license.rst;md5=1dd070c98a281d18d9eefd938729b031"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = "git://github.com/OpenNuvoton/MA35D1_arm-trusted-firmware-v2.3.git;branch=master;protocol=https"
SRC_URI += "file://${TFA_DDR_HEADER}"

SECTION = "bootloaders"
SRCREV = "${TFA_SRCREV}"
TFA_SRCREV ?= "${AUTOREV}"

PV = "${TF_VERSION}+git${SRCPV}"
TF_VERSION = "2.3"

PACKAGE_ARCH = "${MACHINE_ARCH}"

inherit deploy

PROVIDES += "virtual/trusted-firmware-a"
DEPENDS += "dtc-native"
COMPATIBLE_MACHINE = "(ma35d0)"

# Let the Makefile handle setting up the CFLAGS and LDFLAGS as it
# is a standalone application
LDFLAGS[unexport] = "1"
CFLAGS[unexport] = "1"
LD[unexport] = "1"
AS[unexport] = "1"

# Configure ma35d0 make settings
PLATFORM = "${TFA_PLATFORM}"
export CROSS_COMPILE = "${TARGET_PREFIX}"
export ARCH = "arm64"

BOOT_TOOLS = ""

do_compile:prepend() {
    if echo ${TFA_DTB} | grep -q "custom"; then
        cp ${UNPACKDIR}/${TFA_DDR_HEADER} ${S}/plat/nuvoton/ma35d0/include/custom_ddr.h
    fi
}

do_compile() {
    TFA_OPT="NEED_BL31=yes NEED_BL33=yes MA35D0_PMIC=${TFA_PMIC}"

    oe_runmake PLAT=${PLATFORM} ${TFA_OPT} -C ${S} realclean
    oe_runmake PLAT=${PLATFORM} ${TFA_OPT} LDFLAGS="--no-warn-rwx-segments" -C ${S} all
    oe_runmake PLAT=${PLATFORM} ${TFA_OPT} -C ${S} fiptool
}

do_deploy() {
    install -d ${DEPLOYDIR}
    install -Dm 0644 ${S}/build/${PLATFORM}/release/bl2.bin ${DEPLOYDIR}/bl2-${PLATFORM}.bin
    install -Dm 0644 ${S}/build/${PLATFORM}/release/fdts/${TFA_DTB}.dtb ${DEPLOYDIR}/bl2-${PLATFORM}.dtb
    install -Dm 0644 ${S}/build/${PLATFORM}/release/bl31.bin ${DEPLOYDIR}/bl31-${PLATFORM}.bin
    install -Dm 0755 ${S}/tools/fiptool/fiptool ${DEPLOYDIR}/fiptool
}

addtask deploy after do_compile
