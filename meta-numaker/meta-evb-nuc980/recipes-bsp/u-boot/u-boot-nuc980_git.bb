require recipes-bsp/u-boot/u-boot.inc
require recipes-bsp/u-boot/u-boot-common.inc

DESCRIPTION = "U-Boot for Nuvoton NUC980"
SECTION = "bootloaders"
LICENSE = "GPL-2.0-or-later"
LIC_FILES_CHKSUM = "file://Licenses/README;md5=a2c678cfd4a4d97135585cad908541c6"

DEPENDS += "flex-native bison-native python3-native"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = " \
    git://github.com/OpenNuvoton/NUC970_U-Boot_v2016.11.git;protocol=https;branch=master \
    file://patch-uboot-sd.py \
"
SRCREV = "${AUTOREV}"

EXTRA_OEMAKE += ' KCFLAGS="-Wno-error=int-conversion -Wno-error=implicit-function-declaration"'
UBOOT_MACHINE = "nuc980_iot_defconfig"
SPL_BINARY = "spl/u-boot-spl.bin"
PROVIDES += "u-boot"
UBOOT_INITIAL_ENV = ""

do_configure:prepend() {
    # Enable SD1 (Port F, sdh@b0018000) support, fix SDH timeout, and setup default boot environment
    python3 ${UNPACKDIR}/patch-uboot-sd.py "${S}"
}

do_compile:append() {
    # Build SD1 boot U-Boot binary (CONFIG_ENV_IS_IN_MMC at offset 0x80000, size 0x10000)
    mkdir -p ${B}/sd
    cp -f ${B}/.config ${B}/sd/.config
    sed -i 's/^CONFIG_SYS_EXTRA_OPTIONS=.*/CONFIG_SYS_EXTRA_OPTIONS="ENV_IS_IN_MMC"/' ${B}/sd/.config
    sed -i 's/^CONFIG_SPL=y/# CONFIG_SPL is not set/' ${B}/sd/.config
    oe_runmake -C ${S} O=${B}/sd olddefconfig
    oe_runmake -C ${S} O=${B}/sd u-boot.bin
}

do_deploy:append() {
    if [ -f ${B}/sd/u-boot.bin ]; then
        install -m 0644 ${B}/sd/u-boot.bin ${DEPLOYDIR}/u-boot-sd-${MACHINE}-${PV}-${PR}.bin
        ln -sf u-boot-sd-${MACHINE}-${PV}-${PR}.bin ${DEPLOYDIR}/u-boot-sd-${MACHINE}.bin
        ln -sf u-boot-sd-${MACHINE}-${PV}-${PR}.bin ${DEPLOYDIR}/u-boot-sd.bin
    fi
    if [ -f ${DEPLOYDIR}/u-boot-${MACHINE}-${PV}-${PR}.bin ]; then
        ln -sf u-boot-${MACHINE}-${PV}-${PR}.bin ${DEPLOYDIR}/u-boot-spinand-${MACHINE}.bin
        ln -sf u-boot-${MACHINE}-${PV}-${PR}.bin ${DEPLOYDIR}/u-boot-spinand.bin
    fi
}
