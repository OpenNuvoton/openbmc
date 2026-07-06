SUMMARY = "Generate NuWriter pack.bin for NUC980 SPI NAND programming"
DESCRIPTION = "Produces a nuwriter_pack.bin that can be programmed to SPI NAND via NuWriter tool"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit deploy native

DEPENDS += " \
    python3-native \
"

# Depend on deploy outputs from other recipes
do_compile[depends] += " \
    u-boot-nuc980:do_deploy \
    virtual/kernel:do_deploy \
    obmc-phosphor-image:do_image_complete \
"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = " \
    file://nuwriter_pack.py \
    file://nuwriter_unpack.py \
    file://NUC980DK71YC.ini \
    file://uboot-env.txt \
"

S = "${UNPACKDIR}"
DEPLOY_DIR_IMAGE_NUC980 = "${DEPLOY_DIR}/images/${MACHINE}"

do_compile() {
    # KERNEL_DEVICETREE may include subdir prefix (e.g. nuvoton/), use basename
    DTB_FILE=$(basename ${KERNEL_DEVICETREE})

    bbnote "Generating NUC980 nuwriter_pack.bin..."
    python3 ${S}/nuwriter_pack.py -o ${B}/nuwriter_pack.bin \
        -i ${DEPLOY_DIR_IMAGE_NUC980}/u-boot-spl.bin type=loader address=0x0 exec=0x200 ddr=${S}/NUC980DK71YC.ini readstatus=0x0F writestatus=0x1F statusval=0x18 \
        -i ${S}/uboot-env.txt type=env address=0x80000 \
        -i ${DEPLOY_DIR_IMAGE_NUC980}/u-boot.bin type=data address=0x100000 \
        -i ${DEPLOY_DIR_IMAGE_NUC980}/${DTB_FILE} type=data address=0x180000 \
        -i ${DEPLOY_DIR_IMAGE_NUC980}/uImage type=data address=0x200000 \
        -i ${DEPLOY_DIR_IMAGE_NUC980}/obmc-phosphor-image-${MACHINE}.ubi type=data address=0x800000

    if [ ! -f ${B}/nuwriter_pack.bin ]; then
        bbfatal "nuwriter_pack.py failed to generate nuwriter_pack.bin"
    fi
    bbnote "NuWriter nuwriter_pack.bin generated: $(ls -lh ${B}/nuwriter_pack.bin)"
}

do_deploy() {
    install -d ${DEPLOYDIR}
    install -m 0644 ${B}/nuwriter_pack.bin ${DEPLOYDIR}/nuwriter_pack.bin
    install -m 0755 ${S}/nuwriter_unpack.py ${DEPLOYDIR}/
}

addtask deploy after do_compile
