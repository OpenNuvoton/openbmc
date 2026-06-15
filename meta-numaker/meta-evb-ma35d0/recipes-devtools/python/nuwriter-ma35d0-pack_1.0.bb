SUMMARY = "Generate NuWriter pack.bin for MA35D0 SPI NAND programming"
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

# Depend on deploy outputs from other recipes (do_compile uses them)
do_compile[depends] += " \
    tf-a-ma35d0:do_deploy \
    u-boot-ma35d0:do_deploy \
    linux-ma35d0:do_deploy \
    obmc-phosphor-image:do_image_complete \
"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = " \
    file://header-spinand.json \
    file://pack-spinand.json \
    file://install_nuwriter.bat \
    file://nuwriter_program_spinand.bat \
"

S = "${UNPACKDIR}"
DEPLOY_DIR_IMAGE_MA35D0 = "${DEPLOY_DIR}/images/${MACHINE}"

do_compile() {
    # Work in deploy image directory where all images reside
    cd ${DEPLOY_DIR_IMAGE_MA35D0}

    # Copy JSON configs
    install -m 0644 ${S}/header-spinand.json ${DEPLOY_DIR_IMAGE_MA35D0}/
    install -m 0644 ${S}/pack-spinand.json ${DEPLOY_DIR_IMAGE_MA35D0}/

    # Create symlink for rootfs UBI image
    if [ ! -e obmc-phosphor-image.ubi ]; then
        ln -sf obmc-phosphor-image-${MACHINE}.ubi obmc-phosphor-image.ubi
    fi

    # Generate FIP (Firmware Image Package) with BL31 + U-Boot
    bbnote "Generating FIP image..."
    ${DEPLOY_DIR_IMAGE_MA35D0}/fiptool create \
        --soc-fw ${DEPLOY_DIR_IMAGE_MA35D0}/bl31-ma35d0.bin \
        --nt-fw ${DEPLOY_DIR_IMAGE_MA35D0}/u-boot.bin \
        ${DEPLOY_DIR_IMAGE_MA35D0}/fip.bin
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
    if [ -f ${DEPLOY_DIR_IMAGE_MA35D0}/pack/pack.bin ]; then
        install -m 0644 ${DEPLOY_DIR_IMAGE_MA35D0}/pack/pack.bin \
            ${DEPLOYDIR}/nuwriter-pack-${MACHINE}.bin
    fi

    # Deploy header.bin
    if [ -f ${DEPLOY_DIR_IMAGE_MA35D0}/conv/header.bin ]; then
        install -m 0644 ${DEPLOY_DIR_IMAGE_MA35D0}/conv/header.bin \
            ${DEPLOYDIR}/nuwriter-header-${MACHINE}.bin
    fi

    # Deploy Windows batch scripts
    install -m 0755 ${S}/install_nuwriter.bat ${DEPLOYDIR}/
    install -m 0755 ${S}/nuwriter_program_spinand.bat ${DEPLOYDIR}/
}

addtask deploy after do_compile
