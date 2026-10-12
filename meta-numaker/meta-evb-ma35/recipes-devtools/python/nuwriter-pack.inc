# Common NuWriter pack recipe logic for MA35 series
DESCRIPTION = "Produces a pack.bin that can be programmed to SPI NAND, NAND, or SD via NuWriter tool"
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
    file://header-nand.json \
    file://pack-nand.json \
    file://header-sd.json \
    file://pack-sd.json \
    file://install_nuwriter.bat \
    file://nuwriter_program_spinand.bat \
    file://nuwriter_program_nand.bat \
    file://nuwriter_program_sd.bat \
"

S = "${UNPACKDIR}"
DEPLOY_DIR_IMAGE_MA35 = "${DEPLOY_DIR}/images/${MACHINE}"

do_compile() {
    # Work in deploy image directory where all images reside
    cd ${DEPLOY_DIR_IMAGE_MA35}

    # Determine supported boot devices and primary boot media from UBOOT_CONFIG
    HAVE_SPINAND=0
    HAVE_NAND=0
    HAVE_SD=0
    PRIMARY_BOOT=""

    for cfg in ${UBOOT_CONFIG}; do
        case "$cfg" in
            spinand*)
                HAVE_SPINAND=1
                [ -z "$PRIMARY_BOOT" ] && PRIMARY_BOOT="spinand"
                ;;
            nand*)
                HAVE_NAND=1
                [ -z "$PRIMARY_BOOT" ] && PRIMARY_BOOT="nand"
                ;;
            sd*|emmc*)
                HAVE_SD=1
                [ -z "$PRIMARY_BOOT" ] && PRIMARY_BOOT="sd"
                ;;
        esac
    done

    # Fallback to spinand if nothing was determined
    if [ -z "$PRIMARY_BOOT" ]; then
        if [ "$HAVE_SPINAND" = "1" ]; then
            PRIMARY_BOOT="spinand"
        elif [ "$HAVE_NAND" = "1" ]; then
            PRIMARY_BOOT="nand"
        elif [ "$HAVE_SD" = "1" ]; then
            PRIMARY_BOOT="sd"
        fi
    fi

    # Create symlink for rootfs UBI image
    if [ ! -e obmc-phosphor-image.ubi ]; then
        ln -sf obmc-phosphor-image-${MACHINE}.ubi obmc-phosphor-image.ubi
    fi

    # Create symlink for rootfs ext4 image if available
    if [ ! -e rootfs.ext4 ]; then
        ROOTFS_EXT4=$(ls -t ${DEPLOY_DIR_IMAGE_MA35}/obmc-phosphor-image-${MACHINE}*.ext4 ${DEPLOY_DIR_IMAGE_MA35}/*rootfs*.ext4 ${DEPLOY_DIR_IMAGE_MA35}/obmc-phosphor-image-*.ext4 2>/dev/null | grep -v "\.spdx" | head -n1)
        if [ -n "${ROOTFS_EXT4}" ] && [ -f "${ROOTFS_EXT4}" ]; then
            ln -sf $(basename "${ROOTFS_EXT4}") rootfs.ext4
        fi
    fi

    # Copy and patch JSON configs for enabled boot media
    if [ "$HAVE_SPINAND" = "1" ]; then
        install -m 0644 ${S}/header-spinand.json ${DEPLOY_DIR_IMAGE_MA35}/
        install -m 0644 ${S}/pack-spinand.json ${DEPLOY_DIR_IMAGE_MA35}/
        sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/header-spinand.json
        sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/pack-spinand.json
    fi

    if [ "$HAVE_NAND" = "1" ]; then
        install -m 0644 ${S}/header-nand.json ${DEPLOY_DIR_IMAGE_MA35}/
        install -m 0644 ${S}/pack-nand.json ${DEPLOY_DIR_IMAGE_MA35}/
        sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/header-nand.json
        sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/pack-nand.json
    fi

    if [ "$HAVE_SD" = "1" ]; then
        install -m 0644 ${S}/header-sd.json ${DEPLOY_DIR_IMAGE_MA35}/
        install -m 0644 ${S}/pack-sd.json ${DEPLOY_DIR_IMAGE_MA35}/
        sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/header-sd.json
        sed -i "s/bl2-ma35/bl2-${TFA_PLATFORM}/g" ${DEPLOY_DIR_IMAGE_MA35}/pack-sd.json

        # If rootfs.ext4 is not present, exclude it from pack-sd.json
        if [ ! -e rootfs.ext4 ]; then
            bbwarn "rootfs.ext4 not found in ${DEPLOY_DIR_IMAGE_MA35}, excluding from pack-sd.json"
            python3 -c "
import json
with open('${DEPLOY_DIR_IMAGE_MA35}/pack-sd.json', 'r') as f:
    d = json.load(f)
d['image'] = [img for img in d['image'] if img.get('file') != 'rootfs.ext4']
with open('${DEPLOY_DIR_IMAGE_MA35}/pack-sd.json', 'w') as f:
    json.dump(d, f, indent=4)
"
        fi
    fi

    NUWRITER="${RECIPE_SYSROOT_NATIVE}/usr/share/nuwriter/nuwriter.py"
    export PYTHONPATH="${RECIPE_SYSROOT_NATIVE}/usr/lib/python3.14/site-packages:${RECIPE_SYSROOT_NATIVE}/usr/share/nuwriter"

    # Select U-Boot binary for each storage
    UBOOT_SPINAND_BIN="u-boot.bin"
    if [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot.bin-spinand" ]; then
        UBOOT_SPINAND_BIN="u-boot.bin-spinand"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-${MACHINE}.bin-spinand" ]; then
        UBOOT_SPINAND_BIN="u-boot-${MACHINE}.bin-spinand"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-spinand.bin" ]; then
        UBOOT_SPINAND_BIN="u-boot-spinand.bin"
    fi

    UBOOT_NAND_BIN="u-boot.bin"
    if [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot.bin-nand" ]; then
        UBOOT_NAND_BIN="u-boot.bin-nand"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-${MACHINE}.bin-nand" ]; then
        UBOOT_NAND_BIN="u-boot-${MACHINE}.bin-nand"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-nand.bin" ]; then
        UBOOT_NAND_BIN="u-boot-nand.bin"
    fi

    UBOOT_SD_BIN="u-boot.bin"
    if [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot.bin-sd" ]; then
        UBOOT_SD_BIN="u-boot.bin-sd"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-${MACHINE}.bin-sd" ]; then
        UBOOT_SD_BIN="u-boot-${MACHINE}.bin-sd"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-sd.bin" ]; then
        UBOOT_SD_BIN="u-boot-sd.bin"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot.bin-sdcard" ]; then
        UBOOT_SD_BIN="u-boot.bin-sdcard"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-${MACHINE}.bin-sdcard" ]; then
        UBOOT_SD_BIN="u-boot-${MACHINE}.bin-sdcard"
    elif [ -f "${DEPLOY_DIR_IMAGE_MA35}/u-boot-sdcard.bin" ]; then
        UBOOT_SD_BIN="u-boot-sdcard.bin"
    fi

    # Helper function to generate FIP image with specified U-Boot
    generate_fip() {
        src_uboot="$1"
        out_fip="$2"
        bbnote "Generating ${out_fip} with ${src_uboot}..."
        ${DEPLOY_DIR_IMAGE_MA35}/fiptool create \
            --soc-fw ${DEPLOY_DIR_IMAGE_MA35}/bl31-${TFA_PLATFORM}.bin \
            --nt-fw ${DEPLOY_DIR_IMAGE_MA35}/${src_uboot} \
            ${DEPLOY_DIR_IMAGE_MA35}/${out_fip}
        if [ ! -f "${DEPLOY_DIR_IMAGE_MA35}/${out_fip}" ]; then
            bbfatal "fiptool failed to generate ${out_fip}"
        fi
    }

    # Generate SPI-NAND FIP, header, and pack
    if [ "$HAVE_SPINAND" = "1" ]; then
        generate_fip "${UBOOT_SPINAND_BIN}" "fip-spinand.bin"
        cp -f ${DEPLOY_DIR_IMAGE_MA35}/fip-spinand.bin ${DEPLOY_DIR_IMAGE_MA35}/fip.bin

        bbnote "Generating NuWriter SPI-NAND header.bin..."
        python3 ${NUWRITER} -c header-spinand.json
        if [ ! -d conv ] || [ ! -f conv/header.bin ]; then
            bbfatal "nuwriter -c failed to generate conv/header.bin for SPI-NAND"
        fi
        mkdir -p conv-spinand
        cp conv/header.bin conv-spinand/header.bin

        bbnote "Generating NuWriter SPI-NAND pack.bin..."
        python3 ${NUWRITER} -p pack-spinand.json
        if [ ! -d pack ] || [ ! -f pack/pack.bin ]; then
            bbfatal "nuwriter -p failed to generate pack/pack.bin for SPI-NAND"
        fi
        mkdir -p pack-spinand
        cp pack/pack.bin pack-spinand/pack.bin
    fi

    # Generate NAND FIP, header, and pack
    if [ "$HAVE_NAND" = "1" ]; then
        generate_fip "${UBOOT_NAND_BIN}" "fip-nand.bin"
        cp -f ${DEPLOY_DIR_IMAGE_MA35}/fip-nand.bin ${DEPLOY_DIR_IMAGE_MA35}/fip.bin

        bbnote "Generating NuWriter NAND header.bin..."
        python3 ${NUWRITER} -c header-nand.json
        if [ ! -d conv ] || [ ! -f conv/header.bin ]; then
            bbfatal "nuwriter -c failed to generate conv/header.bin for NAND"
        fi
        mkdir -p conv-nand
        cp conv/header.bin conv-nand/header.bin

        bbnote "Generating NuWriter NAND pack.bin..."
        python3 ${NUWRITER} -p pack-nand.json
        if [ ! -d pack ] || [ ! -f pack/pack.bin ]; then
            bbfatal "nuwriter -p failed to generate pack/pack.bin for NAND"
        fi
        mkdir -p pack-nand
        cp pack/pack.bin pack-nand/pack.bin
    fi

    # Generate SD FIP, header, and pack
    if [ "$HAVE_SD" = "1" ]; then
        generate_fip "${UBOOT_SD_BIN}" "fip-sd.bin"
        cp -f ${DEPLOY_DIR_IMAGE_MA35}/fip-sd.bin ${DEPLOY_DIR_IMAGE_MA35}/fip.bin

        bbnote "Generating NuWriter SD header.bin..."
        python3 ${NUWRITER} -c header-sd.json
        if [ ! -d conv ] || [ ! -f conv/header.bin ]; then
            bbfatal "nuwriter -c failed to generate conv/header.bin for SD"
        fi
        mkdir -p conv-sd
        cp conv/header.bin conv-sd/header.bin

        bbnote "Generating NuWriter SD pack.bin..."
        python3 ${NUWRITER} -p pack-sd.json
        if [ ! -d pack ] || [ ! -f pack/pack.bin ]; then
            bbfatal "nuwriter -p failed to generate pack/pack.bin for SD"
        fi
        mkdir -p pack-sd
        cp pack/pack.bin pack-sd/pack.bin
    fi

    # Ensure default fip.bin points to primary boot media
    if [ -n "$PRIMARY_BOOT" ] && [ -f "${DEPLOY_DIR_IMAGE_MA35}/fip-${PRIMARY_BOOT}.bin" ]; then
        cp -f ${DEPLOY_DIR_IMAGE_MA35}/fip-${PRIMARY_BOOT}.bin ${DEPLOY_DIR_IMAGE_MA35}/fip.bin
    fi

    bbnote "NuWriter pack.bin generated successfully"
}

do_deploy() {
    install -d ${DEPLOYDIR}

    # Determine supported boot devices and primary boot media from UBOOT_CONFIG
    HAVE_SPINAND=0
    HAVE_NAND=0
    HAVE_SD=0
    PRIMARY_BOOT=""

    for cfg in ${UBOOT_CONFIG}; do
        case "$cfg" in
            spinand*)
                HAVE_SPINAND=1
                [ -z "$PRIMARY_BOOT" ] && PRIMARY_BOOT="spinand"
                ;;
            nand*)
                HAVE_NAND=1
                [ -z "$PRIMARY_BOOT" ] && PRIMARY_BOOT="nand"
                ;;
            sd*|emmc*)
                HAVE_SD=1
                [ -z "$PRIMARY_BOOT" ] && PRIMARY_BOOT="sd"
                ;;
        esac
    done

    if [ -z "$PRIMARY_BOOT" ]; then
        if [ "$HAVE_SPINAND" = "1" ]; then
            PRIMARY_BOOT="spinand"
        elif [ "$HAVE_NAND" = "1" ]; then
            PRIMARY_BOOT="nand"
        elif [ "$HAVE_SD" = "1" ]; then
            PRIMARY_BOOT="sd"
        fi
    fi

    # Deploy SPI-NAND artifacts
    if [ "$HAVE_SPINAND" = "1" ]; then
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/pack-spinand/pack.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/pack-spinand/pack.bin \
                ${DEPLOYDIR}/nuwriter-pack-spinand-${MACHINE}.bin
        fi
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/conv-spinand/header.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/conv-spinand/header.bin \
                ${DEPLOYDIR}/nuwriter-header-spinand-${MACHINE}.bin
        fi
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/fip-spinand.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/fip-spinand.bin \
                ${DEPLOYDIR}/fip-spinand-${MACHINE}.bin
        fi
        install -m 0755 ${S}/nuwriter_program_spinand.bat ${DEPLOYDIR}/
        sed -i "s/@MACHINE@/${MACHINE}/g" ${DEPLOYDIR}/nuwriter_program_spinand.bat
        sed -i "s/@NUWRITER_DDR_IMG@/${NUWRITER_DDR_IMG}/g" ${DEPLOYDIR}/nuwriter_program_spinand.bat
    fi

    # Deploy NAND artifacts
    if [ "$HAVE_NAND" = "1" ]; then
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/pack-nand/pack.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/pack-nand/pack.bin \
                ${DEPLOYDIR}/nuwriter-pack-nand-${MACHINE}.bin
        fi
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/conv-nand/header.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/conv-nand/header.bin \
                ${DEPLOYDIR}/nuwriter-header-nand-${MACHINE}.bin
        fi
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/fip-nand.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/fip-nand.bin \
                ${DEPLOYDIR}/fip-nand-${MACHINE}.bin
        fi
        install -m 0755 ${S}/nuwriter_program_nand.bat ${DEPLOYDIR}/
        sed -i "s/@MACHINE@/${MACHINE}/g" ${DEPLOYDIR}/nuwriter_program_nand.bat
        sed -i "s/@NUWRITER_DDR_IMG@/${NUWRITER_DDR_IMG}/g" ${DEPLOYDIR}/nuwriter_program_nand.bat
    fi

    # Deploy SD artifacts
    if [ "$HAVE_SD" = "1" ]; then
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/pack-sd/pack.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/pack-sd/pack.bin \
                ${DEPLOYDIR}/nuwriter-pack-sd-${MACHINE}.bin
        fi
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/conv-sd/header.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/conv-sd/header.bin \
                ${DEPLOYDIR}/nuwriter-header-sd-${MACHINE}.bin
        fi
        if [ -f ${DEPLOY_DIR_IMAGE_MA35}/fip-sd.bin ]; then
            install -m 0644 ${DEPLOY_DIR_IMAGE_MA35}/fip-sd.bin \
                ${DEPLOYDIR}/fip-sd-${MACHINE}.bin
        fi
        install -m 0755 ${S}/nuwriter_program_sd.bat ${DEPLOYDIR}/
        sed -i "s/@MACHINE@/${MACHINE}/g" ${DEPLOYDIR}/nuwriter_program_sd.bat
        sed -i "s/@NUWRITER_DDR_IMG@/${NUWRITER_DDR_IMG}/g" ${DEPLOYDIR}/nuwriter_program_sd.bat
    fi

    # Always deploy installer
    install -m 0755 ${S}/install_nuwriter.bat ${DEPLOYDIR}/
}

do_compile[depends] += " \
    virtual/bootloader:do_deploy \
    virtual/trusted-firmware-a:do_deploy \
    virtual/kernel:do_deploy \
    obmc-phosphor-image:do_image_complete \
"
addtask deploy after do_compile before do_build
