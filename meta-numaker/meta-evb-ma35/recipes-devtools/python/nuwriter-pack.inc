# Common NuWriter pack recipe logic for MA35 series
DESCRIPTION = "Produces a pack.bin that can be programmed to SPI NAND via NuWriter tool"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit deploy native

DEPENDS += " \
    python3-nuwriter-native \
    python3-native \
    python3-crcmod-native \
    python3-pycryptodome-native \
    python3-ecdsa-native \
    python3-tqdm-native \
    python3-pyusb-native \
"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = " \
    file://header-spinand.json \
    file://pack-spinand.json \
    file://install_nuwriter.bat \
    file://nuwriter_program_spinand.bat \
"

S = "${UNPACKDIR}"
DEPLOY_DIR_IMAGE_MA35 = "${DEPLOY_DIR}/images/${MACHINE}"

do_compile() {
    # Work in deploy image directory where all images reside
    cd ${DEPLOY_DIR_IMAGE_MA35}

    # Copy JSON configs
    install -m 0644 ${S}/header-spinand.json ${DEPLOY_DIR_IMAGE_MA35}/
    install -m 0644 ${S}/pack-spinand.json ${DEPLOY_DIR_IMAGE_MA35}/

    # Patch bl2 filenames to match TFA_PLATFORM
    sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/header-spinand.json
    sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/pack-spinand.json

    # Create symlink for rootfs UBI image
    if [ ! -e obmc-phosphor-image.ubi ]; then
        ln -sf obmc-phosphor-image-${MACHINE}.ubi obmc-phosphor-image.ubi
    fi

    # Generate FIP (Firmware Image Package) with BL31 + U-Boot
    bbnote "Generating FIP image..."
    ${DEPLOY_DIR_IMAGE_MA35}/fiptool create \
        --soc-fw ${DEPLOY_DIR_IMAGE_MA35}/bl31-${TFA_PLATFORM}.bin \
        --nt-fw ${DEPLOY_DIR_IMAGE_MA35}/u-boot.bin \
        ${DEPLOY_DIR_IMAGE_MA35}/fip.bin
    if [ ! -f fip.bin ]; then
        bbfatal "fiptool failed to generate fip.bin"
    fi
    bbnote "FIP image generated: $(ls -lh fip.bin)"

    NUWRITER="${RECIPE_SYSROOT_NATIVE}/usr/share/nuwriter/nuwriter.py"
    export PYTHONPATH="${RECIPE_SYSROOT_NATIVE}/usr/lib/python3.14/site-packages:${RECIPE_SYSROOT_NATIVE}/usr/share/nuwriter"

    # Generate header.bin (boot header with SPI NAND params and BL2 location)
    bbnote "Generating NuWriter header.bin..."
    python3 ${NUWRITER} -c header-spinand.json
    if [ ! -d conv ] || [ ! -f conv/header.bin ]; then
        bbfatal "nuwriter -c failed to generate conv/header.bin"
    fi

    # Generate pack.bin (all images packed at NAND offsets)
    bbnote "Generating NuWriter pack.bin..."
    python3 ${NUWRITER} -p pack-spinand.json
    if [ ! -d pack ] || [ ! -f pack/pack.bin ]; then
        bbfatal "nuwriter -p failed to generate pack/pack.bin"
    fi

    bbnote "NuWriter pack.bin generated successfully"
}

do_deploy() {
    install -d ${DEPLOYDIR}

    # Deploy pack.bin
    if [ -f ${DEPLOY_DIR_IMAGE_MA35}/pack/pack.bin ]; then
        install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/pack/pack.bin \
            ${DEPLOYDIR}/nuwriter-pack-${MACHINE}.bin
    fi

    # Deploy header.bin
    if [ -f ${DEPLOY_DIR_IMAGE_MA35}/conv/header.bin ]; then
        install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/conv/header.bin \
            ${DEPLOYDIR}/nuwriter-header-${MACHINE}.bin
    fi

    # Deploy Windows batch scripts (patch placeholders with machine-specific values)
    install -m 0755 ${S}/install_nuwriter.bat ${DEPLOYDIR}/
    install -m 0755 ${S}/nuwriter_program_spinand.bat ${DEPLOYDIR}/
    sed -i "s/@MACHINE@/${MACHINE}/g" ${DEPLOYDIR}/nuwriter_program_spinand.bat
    sed -i "s/@NUWRITER_DDR_IMG@/${NUWRITER_DDR_IMG}/g" ${DEPLOYDIR}/nuwriter_program_spinand.bat
}

addtask deploy after do_compile
