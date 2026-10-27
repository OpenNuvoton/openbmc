#@TYPE: Machine Include
#@NAME: Nuvoton MA35 Common
#@DESCRIPTION: Common machine settings for Nuvoton MA35 series SoC (Cortex-A35)

# MA35 series is dual Cortex-A35
DEFAULTTUNE ?= "cortexa35-crypto"
require conf/machine/include/arm/armv8a/tune-cortexa35.inc

MACHINEOVERRIDES =. "ma35:"

# Unified recipe providers for MA35 family
PREFERRED_PROVIDER_virtual/kernel ?= "linux-ma35"
PREFERRED_PROVIDER_virtual/bootloader ?= "u-boot-ma35"
PREFERRED_PROVIDER_u-boot ?= "u-boot-ma35"
PREFERRED_PROVIDER_virtual/trusted-firmware-a ?= "tf-a-ma35"

# Default BMC device tree name follows ${MACHINE}-bmc.dts naming convention
MA35_DTS ?= "${MACHINE}-bmc.dts"

EXTRA_IMAGEDEPENDS += "virtual/bootloader virtual/trusted-firmware-a"

# OpenBMC flash layout for 512MB Flash (Pure UBI Architecture for SPI-NAND and raw NAND)
# MTD partitions:
#   mtd0: (spinand|nand)-uboot   (0x0000000 - 0x00400000, 4MB)   raw (Header+BL2+FIP)
#   mtd1: (spinand|nand)-rootfs  (0x00400000 - 0x20000000, 508MB) UBI Pool
#
# UBI volumes on mtd1 (508MB = 4064 PEBs):
#   Volume 0: u-boot-env (256KiB, pre-loaded 64KB env)
#   Volume 1: kernel-a   (16MiB dynamic)
#   Volume 2: dtb-a      (512KiB dynamic)
#   Volume 3: rofs-a     (100MiB dynamic, ubifs)
#   Volume 4: kernel-b   (16MiB dynamic, OTA standby)
#   Volume 5: dtb-b      (512KiB dynamic, OTA standby)
#   Volume 6: rofs-b     (100MiB dynamic, OTA standby)
#   Volume 7: rwfs       (10MiB autoresize -> fills remaining ~255MB!)

# Default storage architecture: ubi (SPI-NAND / raw NAND) or mmc (eMMC/SD)
MA35_STORAGE_TYPE ??= "ubi"
DISTRO_FEATURES:append = " ${@'obmc-ubi-fs' if d.getVar('MA35_STORAGE_TYPE') == 'ubi' else 'phosphor-mmc'}"

# UBI storage parameters
BMC_RO_MTD:df-obmc-ubi-fs = "spinand-rootfs"
BMC_RW_MTD:df-obmc-ubi-fs = "spinand-rootfs"
BMC_KERNEL_MTD:df-obmc-ubi-fs = "spinand-rootfs"
BMC_RW_SIZE:df-obmc-ubi-fs ?= "0x600000"

# MMC storage parameters (eMMC / SD Card)
WKS_FILE ?= "sdimage-ma35-dual.wks.in"
WKS_FILE_DEPENDS ?= "virtual/kernel virtual/bootloader virtual/trusted-firmware-a"
IMAGE_BOOT_FILES ?= "Image Image.dtb"

FLASH_SIZE = "524288"

# Output both UBI (SPI-NAND / NAND) and EXT4 / WIC (SD / eMMC) disk images
IMAGE_FSTYPES += "ubi ubifs ext4 wic wic.gz"

# UBI image settings for 512MB Flash (508MB rootfs partition = 4064 PEBs)
MKUBIFS_ARGS ?= "-m 2048 -e 126976 -c 3950 -x lzo -F"
UBINIZE_ARGS ?= "-m 2048 -p 131072 -s 2048"
UBI_VOLNAME = "rootfs"

SERIAL_CONSOLES = "115200;ttyS0"

UBOOT_ENTRYPOINT = "0x80E00000"
UBOOT_LOADADDRESS = "0x80E00000"

# No QEMU support for this hardware platform
MACHINE_FEATURES:remove = "qemu-usermode"
EXTRA_IMAGEDEPENDS:remove = "qemu-system-native qemu-helper-native"
IMAGE_CLASSES:remove = "qemuboot"
