DESCRIPTION = "U-Boot for Nuvoton MA35D0K5"
require recipes-bsp/u-boot/u-boot.inc

LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://Licenses/gpl-2.0.txt;md5=b234ee4d69f5fce4486a80fdaf4a4263"

PROVIDES += "u-boot"
DEPENDS += "dtc-native bc-native flex-native bison-native"

unset _PYTHON_SYSCONFIGDATA_NAME

UBOOT_SRC ?= "git://github.com/OpenNuvoton/MA35D1_u-boot-v2020.07.git;branch=master;protocol=https"

SRCREV = "${UBOOT_SRCREV}"
UBOOT_SRCREV ?= "${AUTOREV}"

SRCBRANCH = "2020.07"
SRC_URI = "${UBOOT_SRC}"

PV = "2020.07+git${SRCPV}"
B = "${WORKDIR}/build"
LOCALVERSION ?= "-${SRCBRANCH}"

# Fix SPI-NAND boot: correct UBI partition number and memory size
do_configure:prepend() {
    sed -i 's/spinand_ubiblock=9/spinand_ubiblock=4/' ${S}/include/configs/ma35d0.h
    sed -i 's/nand_ubiblock=9/nand_ubiblock=4/' ${S}/include/configs/ma35d0.h
    sed -i 's|rdinit=/sbin/init|init=/sbin/init|' ${S}/include/configs/ma35d0.h
    sed -i 's/CONFIG_SYS_BOOTM_LEN.*SZ_64M/CONFIG_SYS_BOOTM_LEN\t\t\tSZ_16M/' ${S}/include/configs/ma35d0.h
    sed -i '/mem=256M/s/mem=256M/mem=256M swiotlb=1/' ${S}/include/configs/ma35d0.h
}

COMPATIBLE_MACHINE = "(ma35d05k)"
PACKAGE_ARCH = "${MACHINE_ARCH}"
