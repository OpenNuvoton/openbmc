# Common U-Boot recipe logic for MA35 series
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

# Fix SPI-NAND boot: correct UBI partition number, memory size, and remove UBIFS distro boot probe
do_configure:prepend() {
    for h in ${S}/include/configs/ma35d0.h ${S}/include/configs/ma35d1.h; do
        if [ -f "$h" ]; then
            sed -i 's/spinand_ubiblock=9/spinand_ubiblock=4/' "$h"
            sed -i 's/nand_ubiblock=9/nand_ubiblock=4/' "$h"
            sed -i 's|rdinit=/sbin/init|init=/sbin/init|' "$h"
            sed -i 's/CONFIG_SYS_BOOTM_LEN.*SZ_64M/CONFIG_SYS_BOOTM_LEN\t\t\tSZ_16M/' "$h"
            sed -i 's/#define BOOT_TARGET_UBIFS(func).*/#define BOOT_TARGET_UBIFS(func)/' "$h"
            sed -i '/BOOT_TARGET_UBIFS(func)[[:space:]]*\\/d' "$h"
        fi
    done
    if [ -f "${S}/include/configs/ma35d0.h" ]; then
        sed -i 's/kernelmem=256M\\0/kernelmem=256M swiotlb=1\\0/' ${S}/include/configs/ma35d0.h
    fi
    if [ -f "${S}/include/configs/ma35d1.h" ]; then
        sed -i 's/kernelmem=256M\\0/kernelmem=512M swiotlb=1\\0/' ${S}/include/configs/ma35d1.h
    fi
    if [ -f "${S}/arch/arm/dts/ma35d1.dts" ]; then
        sed -i 's/0x07000000/0x20000000/' ${S}/arch/arm/dts/ma35d1.dts
    fi
    if [ -f "${S}/arch/arm/dts/ma35d0.dts" ]; then
        sed -i 's/0x07000000/0x10000000/' ${S}/arch/arm/dts/ma35d0.dts
    fi
}

PACKAGE_ARCH = "${MACHINE_ARCH}"
