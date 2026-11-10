#!/usr/bin/env python3
import os
import sys

src = sys.argv[1]

# 1. Fix drivers/mmc/nuc980_mmc.c SDH read timeout registers & GPIO card-detect source
mmc_c = os.path.join(src, "drivers/mmc/nuc980_mmc.c")
with open(mmc_c, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

old_read_block = """\t\tif (data->flags == MMC_DATA_READ) {
\t\t\twritel(DITO_IF, REG_EMMCINTSTS);
\t\t\twritel(0xFFFFFF, REG_EMMCTOUT);
\t\t\tsdcsr |= DI_EN;
\t\t\twritel((unsigned int)data->dest, REG_DMACSAR2);"""

new_read_block = """\t\tif (data->flags == MMC_DATA_READ) {
\t\t\twritel(DITO_IF, REG_SDISR);
\t\t\twritel(0xFFFFFF, REG_SDTMOUT);
\t\t\tsdcsr |= DI_EN;
\t\t\twritel((unsigned int)data->dest, REG_DMACSAR2);"""

if old_read_block in text:
    text = text.replace(old_read_block, new_read_block, 1)

if "writel(readl(REG_SDIER) | 0x40000000, REG_SDIER);" not in text:
    text = text.replace(
        "\twritel(SD_EN, REG_SDH_GCTL);\n\twritel(DMACEN, REG_DMACCSR);",
        "\twritel(SD_EN, REG_SDH_GCTL);\n\twritel(DMACEN, REG_DMACCSR);\n\twritel(readl(REG_SDIER) | 0x40000000, REG_SDIER);",
        1,
    )

with open(mmc_c, "w", encoding="utf-8") as f:
    f.write(text)

# 1b. Declare nuc980_mmc_init prototype in board/nuvoton/nuc980/nuc980.c
board_c = os.path.join(src, "board/nuvoton/nuc980/nuc980.c")
with open(board_c, "r", encoding="utf-8", errors="ignore") as f:
    b_text = f.read()

if "extern int nuc980_mmc_init(int priv);" not in b_text:
    b_text = b_text.replace(
        "int board_mmc_init(bd_t *bd)",
        "extern int nuc980_mmc_init(int priv);\n\nint board_mmc_init(bd_t *bd)",
        1,
    )

with open(board_c, "w", encoding="utf-8") as f:
    f.write(b_text)

# 2. Update include/configs/nuc980_iot.h for MMC and default boot environment
iot_h = os.path.join(src, "include/configs/nuc980_iot.h")
with open(iot_h, "r", encoding="utf-8", errors="ignore") as f:
    h_text = f.read()

if "#ifndef CONFIG_ENV_IS_IN_MMC" not in h_text:
    h_text = h_text.replace(
        "#define CONFIG_ENV_IS_IN_NAND",
        "#ifndef CONFIG_ENV_IS_IN_MMC\n#define CONFIG_ENV_IS_IN_NAND\n#endif",
        1,
    )

boot_cfg_block = """
/* Default autoboot commands and fallback environment */
#undef CONFIG_BOOTDELAY
#define CONFIG_BOOTDELAY 1

#ifndef CONFIG_BOOTCOMMAND
#define CONFIG_BOOTCOMMAND "run loadkernel; run loaddtb; bootm 0x8000 - 0x1400000"
#endif

#ifndef CONFIG_EXTRA_ENV_SETTINGS
#ifndef CONFIG_ENV_IS_IN_MMC
#define CONFIG_EXTRA_ENV_SETTINGS \\
\t"bootargs=noinitrd ubi.mtd=3 root=ubi0:rootfs rootfstype=ubifs rw console=ttyS0,115200n8 init=/sbin/init mem=128M\\0" \\
\t"loadkernel=nand read 0x8000 0x200000 0x600000\\0" \\
\t"loaddtb=nand read 0x1400000 0x180000 0x8000\\0"
#else
#define CONFIG_EXTRA_ENV_SETTINGS \\
\t"bootargs=noinitrd root=/dev/mmcblk0p1 rootfstype=ext4 rw rootwait console=ttyS0,115200n8 init=/sbin/init mem=128M\\0" \\
\t"loadkernel=mmc read 0x8000 0x1000 0x3000\\0" \\
\t"loaddtb=mmc read 0x1400000 0xc00 0x40\\0"
#endif
#endif
"""

mmc_cfg_block = """
/* Following block is for MMC/SD1 support */
#ifdef CONFIG_NUC980_MMC
#define CONFIG_DOS_PARTITION
#ifdef CONFIG_ENV_IS_IN_MMC
#define CONFIG_SYS_MMC_ENV_DEV  0
#define CONFIG_ENV_OFFSET       0x80000
#define CONFIG_ENV_SIZE         0x10000
#define CONFIG_ENV_SECT_SIZE    512
#define CONFIG_ENV_OVERWRITE
#endif
#endif
"""

if "CONFIG_SYS_MMC_ENV_DEV" not in h_text:
    h_text = h_text.replace("#define CONFIG_STACKSIZE", boot_cfg_block + mmc_cfg_block + "\n#define CONFIG_STACKSIZE", 1)

with open(iot_h, "w", encoding="utf-8") as f:
    f.write(h_text)

# 3. Enable SD1 (Port F) and MMC/EXT4/FAT commands in configs/nuc980_iot_defconfig
defcfg = os.path.join(src, "configs/nuc980_iot_defconfig")
with open(defcfg, "r", encoding="utf-8", errors="ignore") as f:
    d_text = f.read()

d_text = d_text.replace("CONFIG_BOOTDELAY=3", "CONFIG_BOOTDELAY=1")

replacements = {
    "# CONFIG_CMD_MMC is not set": "CONFIG_CMD_MMC=y",
    "# CONFIG_CMD_EXT2 is not set": "CONFIG_CMD_EXT2=y",
    "# CONFIG_CMD_EXT4 is not set": "CONFIG_CMD_EXT4=y",
    "# CONFIG_CMD_FAT is not set": "CONFIG_CMD_FAT=y",
    "# CONFIG_NUC980_MMC is not set": "CONFIG_MMC=y\nCONFIG_GENERIC_MMC=y\nCONFIG_NUC980_MMC=y\nCONFIG_NUC980_SD_PORT0=y\nCONFIG_DOS_PARTITION=y",
    "# CONFIG_FS_FAT is not set": "CONFIG_FS_FAT=y",
}
for k, v in replacements.items():
    d_text = d_text.replace(k, v)

with open(defcfg, "w", encoding="utf-8") as f:
    f.write(d_text)

# 4. Fix drivers/mtd/spi/spi_nand.c: don't abort page read on ECC warning
spi_nand_c = os.path.join(src, "drivers/mtd/spi/spi_nand.c")
with open(spi_nand_c, "r", encoding="utf-8", errors="ignore") as f:
    s_text = f.read()

old_ecc = """\t\tret = info->params->verify_ecc(status);
\t\tif (ret == ECC_ERR) {
\t\t\tmtd->ecc_stats.failed++;
\t\t\tprintf("ecc err(0x%x) for page read\\n", status);
\t\t\tret = -EBADMSG;
\t\t\tgoto out;
\t\t}"""

new_ecc = """\t\tret = info->params->verify_ecc(status);
\t\tif (ret == ECC_ERR) {
\t\t\tmtd->ecc_stats.failed++;
\t\t\tprintf("ecc err(0x%x) for page read (non-fatal)\\n", status);
\t\t\tret = 0;
\t\t}"""

if old_ecc in s_text:
    s_text = s_text.replace(old_ecc, new_ecc, 1)

old_raw_ecc = """\t\tif (ret == ECC_ERR) {
\t\t\tprintf("ecc err(0x%x) for page read\\n", status);
\t\t\tret = -EBADMSG;
\t\t\tgoto out;
\t\t}"""

new_raw_ecc = """\t\tif (ret == ECC_ERR) {
\t\t\tprintf("ecc err(0x%x) for page read (non-fatal)\\n", status);
\t\t\tret = 0;
\t\t}"""

if old_raw_ecc in s_text:
    s_text = s_text.replace(old_raw_ecc, new_raw_ecc, 1)

with open(spi_nand_c, "w", encoding="utf-8") as f:
    f.write(s_text)
