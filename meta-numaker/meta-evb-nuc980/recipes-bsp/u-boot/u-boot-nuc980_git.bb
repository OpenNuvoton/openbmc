require recipes-bsp/u-boot/u-boot.inc
require recipes-bsp/u-boot/u-boot-common.inc

DESCRIPTION = "U-Boot for Nuvoton NUC980"
SECTION = "bootloaders"
LICENSE = "GPL-2.0-or-later"
LIC_FILES_CHKSUM = "file://Licenses/README;md5=a2c678cfd4a4d97135585cad908541c6"

DEPENDS += "flex-native bison-native"

SRC_URI = "git://github.com/OpenNuvoton/NUC970_U-Boot_v2016.11.git;protocol=https;branch=master"
SRCREV = "${AUTOREV}"

EXTRA_OEMAKE += ' KCFLAGS="-Wno-error=int-conversion"'
UBOOT_MACHINE = "nuc980_iot_defconfig"
SPL_BINARY = "spl/u-boot-spl.bin"
PROVIDES += "u-boot"
UBOOT_INITIAL_ENV = ""

do_configure:prepend() {
    # Set QSPI0 SPI-NAND clock to 75MHz for SPL and U-Boot proper (PCLK0 is 150MHz, divider 1 = 75MHz)
    sed -i 's/writel([0-9]*, SPI_CLKDIV);/writel(1, SPI_CLKDIV);/' ${S}/board/nuvoton/nuc980/wb_spinand.c
    sed -i 's/spi_flash_probe(0, 0, [0-9]*, 3)/spi_flash_probe(0, 0, 75000000, 3)/' ${S}/drivers/mtd/spi/spi_nand.c
}
