#@TYPE: Machine Include
#@NAME: Nuvoton MA35D0
#@DESCRIPTION: Common machine settings for Nuvoton MA35D0 SoC (Cortex-A35)

PREFERRED_PROVIDER_virtual/kernel ?= "linux-ma35d0"
PREFERRED_PROVIDER_virtual/bootloader ?= "u-boot-ma35d0"
PREFERRED_PROVIDER_u-boot ?= "u-boot-ma35d0"
PREFERRED_PROVIDER_virtual/trusted-firmware-a ?= "tf-a-ma35d0"

# MA35D0 is a dual Cortex-A35
DEFAULTTUNE ?= "cortexa35-crypto"
require conf/machine/include/arm/armv8a/tune-cortexa35.inc

EXTRA_IMAGEDEPENDS += "virtual/bootloader virtual/trusted-firmware-a"

# OpenBMC flash layout for 128MB SPI NAND (UBI managed)
# MTD partitions (defined in DTS):
#   mtd0: spinand-uboot      (0 - 3MB)     raw
#   mtd1: spinand-uboot-env  (3MB - 3.75MB) raw
#   mtd2: spinand-device-tree (3.75MB - 4MB) raw
#   mtd3: spinand-kernel     (4MB - 28MB)   raw
#   mtd4: spinand-rootfs     (28MB - end)   UBI volume
#
# UBI volumes on mtd4:
#   rootfs (UBIFS, ~90MB usable)

FLASH_SIZE = "131072"

IMAGE_FSTYPES += "ubi ubifs"

# UBI image settings for 128MB SPI-NAND
# Typical SPI-NAND: 2048+64 page, 128KB erase block
MKUBIFS_ARGS ?= "-m 2048 -e 126976 -c 760 -x lzo"
UBINIZE_ARGS ?= "-m 2048 -p 131072 -s 2048"
UBI_VOLNAME = "rootfs"

SERIAL_CONSOLES = "115200;ttyS0"

UBOOT_ENTRYPOINT = "0x80E00000"
UBOOT_LOADADDRESS = "0x80E00000"

MACHINEOVERRIDES .= ":ma35d0"
