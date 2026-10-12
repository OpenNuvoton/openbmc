#@TYPE: Machine Include
#@NAME: Nuvoton MA35 Common
#@DESCRIPTION: Common machine settings for Nuvoton MA35 series SoC (Cortex-A35)

# MA35 series is dual Cortex-A35
DEFAULTTUNE ?= "cortexa35-crypto"
require conf/machine/include/arm/armv8a/tune-cortexa35.inc

# Unified recipe providers for MA35 family
PREFERRED_PROVIDER_virtual/kernel ?= "linux-ma35"
PREFERRED_PROVIDER_virtual/bootloader ?= "u-boot-ma35"
PREFERRED_PROVIDER_u-boot ?= "u-boot-ma35"
PREFERRED_PROVIDER_virtual/trusted-firmware-a ?= "tf-a-ma35"

# Default BMC device tree name follows ${MACHINE}-bmc.dts naming convention
MA35_DTS ?= "${MACHINE}-bmc.dts"

EXTRA_IMAGEDEPENDS += "virtual/bootloader virtual/trusted-firmware-a"

# OpenBMC flash layout for 512MB SPI NAND (UBI managed)
# MTD partitions (defined in DTS):
#   mtd0: spinand-uboot       (0x000000 - 0x300000, 3MB)      raw
#   mtd1: spinand-uboot-env   (0x300000 - 0x3C0000, 768KB)    raw
#   mtd2: spinand-device-tree (0x3C0000 - 0x400000, 256KB)    raw
#   mtd3: spinand-kernel      (0x400000 - 0x1C00000, 24MB)    raw
#   mtd4: spinand-rootfs      (0x1C00000 - 0x10000000, 228MB) UBI volume
#
# UBI volumes on mtd4:
#   rootfs (UBIFS, ~200MB usable)

FLASH_SIZE = "524288"

IMAGE_FSTYPES += "ubi ubifs ext4"

# UBI image settings for 512MB SPI-NAND
# SPI-NAND: 2048+64 page, 128KB erase block
# mtd4 = 484MB = 3872 PEBs, ~3800 usable LEBs after UBI overhead
MKUBIFS_ARGS ?= "-m 2048 -e 126976 -c 3800 -x lzo -F"
UBINIZE_ARGS ?= "-m 2048 -p 131072 -s 2048"
UBI_VOLNAME = "rootfs"

SERIAL_CONSOLES = "115200;ttyS0"

UBOOT_ENTRYPOINT = "0x80E00000"
UBOOT_LOADADDRESS = "0x80E00000"

# No QEMU support for this hardware platform
MACHINE_FEATURES:remove = "qemu-usermode"
EXTRA_IMAGEDEPENDS:remove = "qemu-system-native qemu-helper-native"
IMAGE_CLASSES:remove = "qemuboot"
