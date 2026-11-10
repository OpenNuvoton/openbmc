SUMMARY = "Generate NuWriter pack.bin for NUC980 SPI NAND and SD1/eMMC programming"
DESCRIPTION = "Produces nuwriter-pack-spinand and nuwriter-pack-sd (plus bootable SD .wic) for NUC980 using NUC980_PyNuWriter"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit deploy native

DEPENDS += " \
    python3-nuwriter-native \
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
    file://pack-spinand.json \
    file://pack-sd.json \
    file://uboot-env.txt \
    file://uboot-env-sd.txt \
    file://install_nuwriter.bat \
    file://nuwriter_program_spinand.bat \
    file://nuwriter_program_sd.bat \
"

S = "${UNPACKDIR}"
B = "${WORKDIR}/build"
do_compile[dirs] = "${B}"
DEPLOY_DIR_IMAGE_NUC980 = "${DEPLOY_DIR}/images/${MACHINE}"
NUWRITER_DDR_IMG ?= "NUC980DK71YC.ini"

do_compile() {
    NUWRITER="${RECIPE_SYSROOT_NATIVE}/usr/share/nuwriter/nuwriter.py"
    export PYTHONPATH="${RECIPE_SYSROOT_NATIVE}/usr/share/nuwriter:${PYTHONPATH}"

    # KERNEL_DEVICETREE may include subdir prefix (e.g. nuvoton/), use basename
    DTB_FILE=$(basename ${KERNEL_DEVICETREE})

    bbnote "Generating NUC980 SPI-NAND nuwriter-pack-spinand-${MACHINE}.bin via NUC980_PyNuWriter..."
    sed -e "s|@DEPLOY_DIR_IMAGE@|${DEPLOY_DIR_IMAGE_NUC980}|g" \
        -e "s|@UNPACKDIR@|${S}|g" \
        -e "s|@DTB_FILE@|${DTB_FILE}|g" \
        -e "s|@MACHINE@|${MACHINE}|g" \
        ${S}/pack-spinand.json > ${B}/pack-spinand.json

    python3 ${NUWRITER} -p ${B}/pack-spinand.json --output ${B}/nuwriter-pack-spinand-${MACHINE}.bin

    if [ ! -f ${B}/nuwriter-pack-spinand-${MACHINE}.bin ]; then
        bbfatal "NUC980_PyNuWriter failed to generate nuwriter-pack-spinand-${MACHINE}.bin"
    fi
    cp -f ${B}/nuwriter-pack-spinand-${MACHINE}.bin ${B}/nuwriter-pack.bin
    bbnote "NuWriter SPI-NAND pack generated: $(ls -lh ${B}/nuwriter-pack-spinand-${MACHINE}.bin)"

    # Generate SD1/eMMC (sdh@b0018000, Port F) NuWriter pack and raw bootable WIC image
    UBOOT_SD_BIN="${DEPLOY_DIR_IMAGE_NUC980}/u-boot-sd.bin"
    if [ ! -f "${UBOOT_SD_BIN}" ]; then
        UBOOT_SD_BIN="${DEPLOY_DIR_IMAGE_NUC980}/u-boot.bin"
    fi

    ROOTFS_EXT4="${DEPLOY_DIR_IMAGE_NUC980}/obmc-phosphor-image-${MACHINE}.ext4"
    if [ ! -f "${ROOTFS_EXT4}" ]; then
        ROOTFS_EXT4=$(ls -t ${DEPLOY_DIR_IMAGE_NUC980}/obmc-phosphor-image-${MACHINE}*.ext4 2>/dev/null | grep -v "\.spdx" | head -n1)
    fi

    if [ -n "${ROOTFS_EXT4}" ] && [ -f "${ROOTFS_EXT4}" ]; then
        # Generate 512-byte DOS MBR with Partition 1 (type 0x83 Linux) starting at LBA 0x4000 (8 MiB = 0x800000)
        python3 - "${B}/mbr-sd.bin" "${ROOTFS_EXT4}" <<'EOF'
import os, struct, sys
mbr_path, rootfs_path = sys.argv[1], sys.argv[2]
part_sectors = (os.path.getsize(rootfs_path) + 511) // 512
mbr = bytearray(512)
struct.pack_into('<I', mbr, 440, 0x4E393830)
struct.pack_into('<BBBBBBBBII', mbr, 446, 0x00, 0xFE, 0xFF, 0xFF, 0x83, 0xFE, 0xFF, 0xFF, 0x4000, part_sectors)
mbr[510] = 0x55
mbr[511] = 0xAA
with open(mbr_path, 'wb') as f:
    f.write(mbr)
EOF

        bbnote "Generating NUC980 SD1/eMMC nuwriter-pack-sd-${MACHINE}.bin via NUC980_PyNuWriter..."
        sed -e "s|@DEPLOY_DIR_IMAGE@|${DEPLOY_DIR_IMAGE_NUC980}|g" \
            -e "s|@UNPACKDIR@|${S}|g" \
            -e "s|@UBOOT_SD_BIN@|${UBOOT_SD_BIN}|g" \
            -e "s|@MBR_SD_BIN@|${B}/mbr-sd.bin|g" \
            -e "s|@DTB_FILE@|${DTB_FILE}|g" \
            -e "s|@ROOTFS_EXT4@|${ROOTFS_EXT4}|g" \
            ${S}/pack-sd.json > ${B}/pack-sd.json

        python3 ${NUWRITER} -p ${B}/pack-sd.json --output ${B}/nuwriter-pack-sd-${MACHINE}.bin

        if [ ! -f ${B}/nuwriter-pack-sd-${MACHINE}.bin ]; then
            bbfatal "NUC980_PyNuWriter failed to generate nuwriter-pack-sd-${MACHINE}.bin"
        fi
        cp -f ${B}/nuwriter-pack-sd-${MACHINE}.bin ${B}/nuwriter-pack-sd.bin
        bbnote "NuWriter SD1/eMMC pack generated: $(ls -lh ${B}/nuwriter-pack-sd-${MACHINE}.bin)"

        # Assemble direct-bootable raw SD/MMC disk image (.wic) from the NUC980_PyNuWriter SD pack
        python3 - "${B}/nuwriter-pack-sd-${MACHINE}.bin" "${B}/obmc-phosphor-image-${MACHINE}.wic" <<'EOF'
import struct, sys
import nuwriter

pack_path, wic_path = sys.argv[1], sys.argv[2]
with open(pack_path, 'rb') as f:
    children = nuwriter.parse_pack(f.read())

segments = []
max_end = 0
for header, payload, kind in children:
    if kind == 3:
        continue
    length, offset, image_type, _ = struct.unpack('<4I', header)
    if kind == 2 and offset == 0:
        offset = 0x400
    max_end = max(max_end, offset + len(payload))
    segments.append((offset, payload))

total_size = ((max_end + 511) // 512) * 512
with open(wic_path, 'wb') as f:
    f.truncate(total_size)
    for offset, payload in segments:
        f.seek(offset)
        f.write(payload)
print(f"SD WIC image created: {wic_path} ({total_size} bytes)")
EOF
    else
        bbfatal "Missing ext4 rootfs image for SD1/eMMC pack generation in ${DEPLOY_DIR_IMAGE_NUC980}"
    fi
}

do_deploy() {
    install -d ${DEPLOYDIR}
    install -m 0644 ${B}/nuwriter-pack-spinand-${MACHINE}.bin ${DEPLOYDIR}/nuwriter-pack-spinand-${MACHINE}.bin
    install -m 0644 ${B}/nuwriter-pack.bin ${DEPLOYDIR}/nuwriter-pack.bin
    ln -sf nuwriter-pack-spinand-${MACHINE}.bin ${DEPLOYDIR}/nuwriter-pack-${MACHINE}.bin

    if [ -f ${B}/nuwriter-pack-sd-${MACHINE}.bin ]; then
        install -m 0644 ${B}/nuwriter-pack-sd-${MACHINE}.bin ${DEPLOYDIR}/nuwriter-pack-sd-${MACHINE}.bin
        install -m 0644 ${B}/nuwriter-pack-sd.bin ${DEPLOYDIR}/nuwriter-pack-sd.bin
    fi

    if [ -f ${B}/obmc-phosphor-image-${MACHINE}.wic ]; then
        install -m 0644 ${B}/obmc-phosphor-image-${MACHINE}.wic ${DEPLOYDIR}/obmc-phosphor-image-${MACHINE}.wic
    fi

    install -m 0755 ${S}/install_nuwriter.bat ${DEPLOYDIR}/
    install -m 0755 ${S}/nuwriter_program_spinand.bat ${DEPLOYDIR}/
    sed -i "s/@MACHINE@/${MACHINE}/g" ${DEPLOYDIR}/nuwriter_program_spinand.bat
    sed -i "s/@NUWRITER_DDR_IMG@/${NUWRITER_DDR_IMG}/g" ${DEPLOYDIR}/nuwriter_program_spinand.bat

    install -m 0755 ${S}/nuwriter_program_sd.bat ${DEPLOYDIR}/
    sed -i "s/@MACHINE@/${MACHINE}/g" ${DEPLOYDIR}/nuwriter_program_sd.bat
    sed -i "s/@NUWRITER_DDR_IMG@/${NUWRITER_DDR_IMG}/g" ${DEPLOYDIR}/nuwriter_program_sd.bat
}

addtask deploy after do_compile
