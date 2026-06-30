SUMMARY = "Nuvoton NuWriter tool for MA35 series SPI NAND programming"
LICENSE = "GPL-3.0-only"
LIC_FILES_CHKSUM = "file://LICENSE;md5=e49f4652534af377a713df3d9dec60cb"

inherit native

SRC_URI = "git://github.com/OpenNuvoton/MA35D1_NuWriter.git;protocol=https;branch=master"
SRCREV = "${AUTOREV}"

DEPENDS += " \
    python3-native \
    python3-crcmod-native \
    python3-pycryptodome-native \
    python3-ecdsa-native \
    python3-tqdm-native \
    python3-pyusb-native \
"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${datadir}/nuwriter
    install -d ${D}${datadir}/nuwriter/ddrimg

    # Install main scripts
    install -m 0755 ${S}/nuwriter.py ${D}${datadir}/nuwriter/
    install -m 0644 ${S}/xusbcom.py ${D}${datadir}/nuwriter/
    install -m 0644 ${S}/UnpackImage.py ${D}${datadir}/nuwriter/

    # Install DDR images and xusb
    if [ -d ${S}/ddrimg ]; then
        cp -r ${S}/ddrimg/* ${D}${datadir}/nuwriter/ddrimg/
    fi
    if [ -f ${S}/xusb.bin ]; then
        install -m 0644 ${S}/xusb.bin ${D}${datadir}/nuwriter/
    fi

    # Create a wrapper script
    cat > ${D}${bindir}/nuwriter <<'EOF'
#!/bin/sh
exec python3 ${datadir}/nuwriter/nuwriter.py "$@"
EOF
    chmod 0755 ${D}${bindir}/nuwriter
}

# Fix the wrapper path at install time
SYSROOT_DIRS += "${datadir}"
