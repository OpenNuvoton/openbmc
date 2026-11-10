SUMMARY = "Nuvoton NuWriter Python CLI and pack tool for NUC980 series"
DESCRIPTION = "NUC980 Windows NuWriter protocol and pack generator with a MA35-style Python/CLI interface"
HOMEPAGE = "https://github.com/wosayttn/NUC980_PyNuWriter"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit native

SRC_URI = "git://github.com/wosayttn/NUC980_PyNuWriter.git;protocol=https;branch=main"
SRCREV = "${AUTOREV}"

DEPENDS += " \
    python3-native \
    python3-pyusb-native \
"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${datadir}/nuwriter
    install -d ${D}${datadir}/nuwriter/sys_cfg
    install -d ${D}${datadir}/nuwriter/xusb

    # Install main CLI/API script and optional helper hooks
    install -m 0755 ${S}/nuwriter.py ${D}${datadir}/nuwriter/
    if [ -f ${S}/pre-attach-hook.py ]; then
        install -m 0755 ${S}/pre-attach-hook.py ${D}${datadir}/nuwriter/
    fi
    if [ -f ${S}/ch341_reset_uart.py ]; then
        install -m 0755 ${S}/ch341_reset_uart.py ${D}${datadir}/nuwriter/
    fi

    # Install DDR sys_cfg INI files and XUSB firmware binaries
    if [ -d ${S}/sys_cfg ]; then
        cp -r ${S}/sys_cfg/* ${D}${datadir}/nuwriter/sys_cfg/
    fi
    if [ -d ${S}/xusb ]; then
        cp -r ${S}/xusb/* ${D}${datadir}/nuwriter/xusb/
    fi

    # Create CLI wrapper script
    cat > ${D}${bindir}/nuwriter <<'EOF'
#!/bin/sh
exec python3 ${datadir}/nuwriter/nuwriter.py "$@"
EOF
    chmod 0755 ${D}${bindir}/nuwriter
}

SYSROOT_DIRS += "${datadir}"

