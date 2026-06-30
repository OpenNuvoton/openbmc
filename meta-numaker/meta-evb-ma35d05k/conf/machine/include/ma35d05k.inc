#@TYPE: Machine Include
#@NAME: Nuvoton MA35D0K5
#@DESCRIPTION: Common machine settings for Nuvoton MA35D0K5 SoC (Cortex-A35)

PREFERRED_PROVIDER_virtual/kernel ?= "linux-ma35d05k"
PREFERRED_PROVIDER_virtual/bootloader ?= "u-boot-ma35d05k"
PREFERRED_PROVIDER_u-boot ?= "u-boot-ma35d05k"
PREFERRED_PROVIDER_virtual/trusted-firmware-a ?= "tf-a-ma35d05k"

# MA35D0K5 is a dual Cortex-A35
DEFAULTTUNE ?= "cortexa35-crypto"
require conf/machine/include/arm/armv8a/tune-cortexa35.inc

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

IMAGE_FSTYPES += "ubi ubifs"

# UBI image settings for 512MB SPI-NAND
# SPI-NAND: 2048+64 page, 128KB erase block
# mtd4 = 228MB = 1824 PEBs, ~1750 usable LEBs after UBI overhead
MKUBIFS_ARGS ?= "-m 2048 -e 126976 -c 1750 -x lzo"
UBINIZE_ARGS ?= "-m 2048 -p 131072 -s 2048"
UBI_VOLNAME = "rootfs"

SERIAL_CONSOLES = "115200;ttyS0"

UBOOT_ENTRYPOINT = "0x80E00000"
UBOOT_LOADADDRESS = "0x80E00000"

MACHINEOVERRIDES .= ":ma35d05k"
