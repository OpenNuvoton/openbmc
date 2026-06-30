# Copyright 2025 Nuvoton
# Released under the MIT license (see COPYING.MIT for the terms)

SUMMARY = "Linux Kernel for Nuvoton MA35D0K5"
DESCRIPTION = "Linux Kernel provided and supported by Nuvoton for MA35D0K5 SoC (OpenBMC)"

inherit kernel

LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=6bc538ed5bd9a7fc9398086aedcd7e46"

MA35D0_KERNEL_LOADADDR = "0x80080000"
KERNEL_EXTRA_ARGS += "LOADADDR=${MA35D0_KERNEL_LOADADDR}"

KERNEL_SRC ?= "git://github.com/OpenNuvoton/MA35D1_linux-6.6.y.git;branch=master;protocol=https"
SRC_URI = "${KERNEL_SRC}"
SRC_URI += "file://ma35d05k_bmc_defconfig"
SRC_URI += "file://ma35d05k-iot-ma35d05ki1-v1-256m.dts"
SRC_URI += "file://0001-dma-ma35d05k-fix-swiotlb-leak.patch"
SRCREV = "${KERNEL_SRCREV}"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

KERNEL_SRCREV ?= "${AUTOREV}"

SRCBRANCH = "6.6.93"
LOCALVERSION = "-ma35d05k-openbmc"

PV = "${SRCBRANCH}+git${SRCPV}"
S = "${UNPACKDIR}/${BP}"
B = "${WORKDIR}/build"

DEFAULT_PREFERENCE = "1"
DEPENDS += "util-linux-native libyaml-native openssl-native"

KERNEL_IMAGETYPE = "Image"

do_configure:prepend() {
    bbnote "Using BMC-optimized defconfig"
    cp ${UNPACKDIR}/ma35d05k_bmc_defconfig ${UNPACKDIR}/defconfig

    # Replace upstream DTS with BMC-merged version (UBI/UBIFS boot, LED, PDMA)
    cp ${UNPACKDIR}/ma35d05k-iot-ma35d05ki1-v1-256m.dts \
        ${S}/arch/arm64/boot/dts/nuvoton/ma35d0-iot-ma35d05ki1-v1-256m.dts

    # Expand SPI-NAND rootfs partition for 256MB flash
    # Original: 0x6400000 (100MB), New: 0x1E400000 (484MB)
    sed -i '/spinand-rootfs/{n;s|reg = <0x1c00000 0x6400000>|reg = <0x1c00000 0x1E400000>|}' \
        ${S}/arch/arm64/boot/dts/nuvoton/ma35d05k.dtsi
}

do_deploy:append() {
    for dtbf in ${KERNEL_DEVICETREE}; do
        dtb=`normalize_dtb "$dtbf"`
        dtb_ext=${dtb##*.}
        dtb_base_name=`basename $dtb .$dtb_ext`
        ln -sf $dtb_base_name.dtb ${DEPLOYDIR}/Image.dtb
    done
}

COMPATIBLE_MACHINE = "(ma35d05k)"

# Suppress buildpaths QA for kernel debug sources (common for out-of-tree builds)
ERROR_QA:remove = "buildpaths"
WARN_QA:append = " buildpaths"
