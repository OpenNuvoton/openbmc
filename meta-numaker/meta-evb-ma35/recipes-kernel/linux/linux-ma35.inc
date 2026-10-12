# Copyright 2025 Nuvoton
# Released under the MIT license (see COPYING.MIT for the terms)
#
# Common Linux kernel recipe logic for MA35 series

inherit kernel

LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=6bc538ed5bd9a7fc9398086aedcd7e46"

MA35_KERNEL_LOADADDR ?= "0x80080000"
KERNEL_EXTRA_ARGS += "LOADADDR=${MA35_KERNEL_LOADADDR}"

KERNEL_SRC ?= "git://github.com/OpenNuvoton/MA35D1_linux-6.6.y.git;branch=master;protocol=https"
SRC_URI = "${KERNEL_SRC}"
SRC_URI += "file://${MA35_DEFCONFIG}"
SRC_URI += "file://${MA35_DTS}"
SRCREV = "${KERNEL_SRCREV}"

SRCBRANCH = "6.6.93"
LINUX_MAJOR_VERSION = "${@'.'.join((d.getVar('SRCBRANCH') or '6.6').split('.')[:2])}"
FILESEXTRAPATHS:prepend := "${THISDIR}/linux-ma35-${LINUX_MAJOR_VERSION}:${THISDIR}/files:"

KERNEL_SRCREV ?= "${AUTOREV}"

PV = "${SRCBRANCH}+git${SRCPV}"
S = "${UNPACKDIR}/${BP}"
B = "${WORKDIR}/build"

DEFAULT_PREFERENCE = "1"
DEPENDS += "util-linux-native libyaml-native openssl-native"

KERNEL_IMAGETYPE = "Image"

do_configure:prepend() {
    bbnote "Using BMC-optimized defconfig"
    cp ${UNPACKDIR}/${MA35_DEFCONFIG} ${UNPACKDIR}/defconfig

    # Replace upstream DTS with our BMC-customized version
    cp ${UNPACKDIR}/${MA35_DTS} \
        ${S}/arch/arm64/boot/dts/nuvoton/${MA35_DTS_TARGET}

    # Expand SPI-NAND and raw NAND rootfs partitions for 512MB flash
    # Original: 0x6400000 (100MB) or 0x0, New: 0x1E400000 (484MB)
    sed -i -E '/(spinand|nand)-rootfs/{n;s|reg = <0x1[cC]00000 0x[0-9a-fA-F]+>|reg = <0x1c00000 0x1E400000>|}' \
        ${S}/arch/arm64/boot/dts/nuvoton/${MA35_DTSI}
}

do_deploy:append() {
    for dtbf in ${KERNEL_DEVICETREE}; do
        dtb=`normalize_dtb "$dtbf"`
        dtb_ext=${dtb##*.}
        dtb_base_name=`basename $dtb .$dtb_ext`
        ln -sf $dtb_base_name.dtb ${DEPLOYDIR}/Image.dtb
    done
}

# Suppress buildpaths QA for kernel debug sources (common for out-of-tree builds)
ERROR_QA:remove = "buildpaths"
WARN_QA:append = " buildpaths"
