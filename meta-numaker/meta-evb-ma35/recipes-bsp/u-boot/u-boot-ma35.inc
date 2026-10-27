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

SRC_URI = "${UBOOT_SRC} \
           file://patch-uboot-configs.py"

PV = "2020.07+git${SRCPV}"
B = "${WORKDIR}/build"
LOCALVERSION ?= "-${SRCBRANCH}"

# Configure U-Boot for Scheme A (Unified UBI Pool) & Dual Bank fail-safe boot
do_configure:prepend() {
    if [ -f "${UNPACKDIR}/patch-uboot-configs.py" ]; then
        python3 "${UNPACKDIR}/patch-uboot-configs.py" "${S}"
    else
        python3 "${WORKDIR}/patch-uboot-configs.py" "${S}"
    fi
    for defcfg in ${S}/configs/*spinand_defconfig; do
        if [ -f "$defcfg" ]; then
            sed -i 's|CONFIG_MTDPARTS_DEFAULT=.*|CONFIG_MTDPARTS_DEFAULT="mtdparts=spi-nand0:4m(uboot),-(rootfs)"|' "$defcfg"
            sed -i 's/CONFIG_ENV_UBI_PART=".*"/CONFIG_ENV_UBI_PART="rootfs"/' "$defcfg"
            sed -i 's/CONFIG_ENV_UBI_VOLUME=".*"/CONFIG_ENV_UBI_VOLUME="u-boot-env"/' "$defcfg"
            sed -i '/CONFIG_BOOTCOUNT/d' "$defcfg"
            echo "CONFIG_BOOTCOUNT_LIMIT=y" >> "$defcfg"
            echo "CONFIG_BOOTCOUNT_ENV=y" >> "$defcfg"
        fi
    done
    for defcfg in ${S}/configs/*nand_defconfig; do
        if echo "$defcfg" | grep -q "spinand"; then
            continue
        fi
        if [ -f "$defcfg" ]; then
            sed -i 's|CONFIG_MTDPARTS_DEFAULT=.*|CONFIG_MTDPARTS_DEFAULT="mtdparts=nand0:4m(uboot),-(rootfs)"|' "$defcfg"
            sed -i 's/CONFIG_ENV_IS_IN_NAND=y/CONFIG_ENV_IS_IN_UBI=y/' "$defcfg"
            sed -i '/CONFIG_ENV_OFFSET/d' "$defcfg"
            sed -i '/CONFIG_ENV_UBI/d' "$defcfg"
            echo 'CONFIG_ENV_UBI_PART="rootfs"' >> "$defcfg"
            echo 'CONFIG_ENV_UBI_VOLUME="u-boot-env"' >> "$defcfg"
            sed -i '/CONFIG_BOOTCOUNT/d' "$defcfg"
            echo "CONFIG_BOOTCOUNT_LIMIT=y" >> "$defcfg"
            echo "CONFIG_BOOTCOUNT_ENV=y" >> "$defcfg"
        fi
    done
    for dts in ${S}/arch/arm/dts/ma35d0*.dts; do
        if [ -f "$dts" ]; then
            sed -i 's/0x07000000/0x10000000/' "$dts"
        fi
    done
    for dts in ${S}/arch/arm/dts/ma35d1*.dts; do
        if [ -f "$dts" ]; then
            sed -i 's/0x07000000/0x20000000/' "$dts"
        fi
    done
}

do_configure:append() {
    for cfg in ${B}/.config ${B}/*/.config; do
        if [ -f "$cfg" ]; then
            sed -i '/CONFIG_BOOTCOUNT/d' "$cfg"
            echo "CONFIG_BOOTCOUNT_LIMIT=y" >> "$cfg"
            echo "CONFIG_BOOTCOUNT_ENV=y" >> "$cfg"
        fi
    done
}

PACKAGE_ARCH = "${MACHINE_ARCH}"
