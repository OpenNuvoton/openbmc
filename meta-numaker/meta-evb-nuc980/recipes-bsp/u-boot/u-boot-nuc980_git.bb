require recipes-bsp/u-boot/u-boot.inc
require recipes-bsp/u-boot/u-boot-common.inc

DESCRIPTION = "U-Boot for Nuvoton NUC980"
SECTION = "bootloaders"
LICENSE = "GPL-2.0-or-later"
LIC_FILES_CHKSUM = "file://Licenses/README;md5=a2c678cfd4a4d97135585cad908541c6"

DEPENDS += "flex-native bison-native"

SRC_URI = "git://github.com/OpenNuvoton/NUC970_U-Boot_v2016.11.git;protocol=https;branch=master"
SRCREV = "${AUTOREV}"

EXTRA_OEMAKE += ' KCFLAGS="-Wno-error=int-conversion"'
UBOOT_MACHINE = "nuc980_iot_defconfig"
SPL_BINARY = "spl/u-boot-spl.bin"
PROVIDES += "u-boot"
UBOOT_INITIAL_ENV = ""
