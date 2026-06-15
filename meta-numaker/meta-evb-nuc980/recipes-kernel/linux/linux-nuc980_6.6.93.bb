DESCRIPTION = "Linux kernel for Nuvoton NUC980"
SECTION = "kernel"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=6bc538ed5bd9a7fc9398086aedcd7e46"

PROVIDES += "virtual/kernel"

KBRANCH = "master"
SRC_URI = "git://github.com/OpenNuvoton/NUC980-linux-6.6.y.git;protocol=https;branch=${KBRANCH} \
    file://defconfig \
    file://nuc980-iot-128m-bmc.dts \
"
SRCREV = "${AUTOREV}"

PV = "6.6.93+git${SRCPV}"

S = "${WORKDIR}/git"

inherit kernel
require recipes-kernel/linux/linux-yocto.inc

EXTRA_OEMAKE += " KCFLAGS=-Wno-error LOADADDR=${UBOOT_LOADADDRESS}"
KCONFIG_MODE = "--alldefconfig"

KERNEL_VERSION_SANITY_SKIP = "1"

do_patch:append() {
    # Install BMC DTS into kernel source
    install -m 0644 ${UNPACKDIR}/nuc980-iot-128m-bmc.dts ${S}/arch/arm/boot/dts/nuvoton/nuc980-iot-128m-bmc.dts

    # Register the new DTB in the Makefile
    if ! grep -q "nuc980-iot-128m-bmc" ${S}/arch/arm/boot/dts/nuvoton/Makefile; then
        sed -i '/nuc980-iot-g2-v1.0.dtb/a\\tnuc980-iot-128m-bmc.dtb \\' ${S}/arch/arm/boot/dts/nuvoton/Makefile
    fi
}

do_configure:append() {
    sed -i 's/CONFIG_INITRAMFS_SOURCE="..\/rootfs"/CONFIG_INITRAMFS_SOURCE=""/g' ${B}/.config
    sed -i 's/cp $@   ..\/image\/980image/echo "Skipped copy to 980image"/g' ${S}/arch/arm/boot/Makefile
}
