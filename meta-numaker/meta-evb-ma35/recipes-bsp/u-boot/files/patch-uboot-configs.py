#!/usr/bin/env python3
#
# Helper script to configure U-Boot headers for MA35 Pure UBI Architecture
# Both SPI-NAND and raw NAND boot directly from UBI volumes:
#   kernel-a / kernel-b, dtb-a / dtb-b, rofs-a / rofs-b
#
import os
import sys
import re

def patch_configs(s_dir):
    new_spinandargs = (
        "#define SPINANDARGS \\\n"
        "\t\"spinandboot=\" \\\n"
        "\t\t\"mtd list; \" \\\n"
        "\t\t\"if test \\\"${mtdids}\\\" = \\\"nand0=nand0\\\"; then run nandboot; else \" \\\n"
        "\t\t\"if test -z \\\"${bootubipart}\\\"; then setenv bootubipart rootfs; fi; \" \\\n"
        "\t\t\"ubi part ${bootubipart}; \" \\\n"
        "\t\t\"if ubi read ${loadaddr} u-boot-env 0x10000; then env import -c ${loadaddr} 0x10000; fi; \" \\\n"
        "\t\t\"if test -z \\\"${bootubivol}\\\"; then setenv bootubivol rofs-a; fi; \" \\\n"
        "\t\t\"if test -z \\\"${kernelname}\\\"; then setenv kernelname kernel-a; fi; \" \\\n"
        "\t\t\"if test -z \\\"${dtbname}\\\"; then setenv dtbname dtb-a; fi; \" \\\n"
        "\t\t\"echo \\\"Booting from spinand (${kernelname}, ${dtbname}, ${bootubivol}) ...\\\"; \" \\\n"
        "\t\t\"setenv bootargs noinitrd ubi.mtd=${spinand_ubiblock} root=ubi0:${bootubivol} rootfstype=ubifs rw rootwait=1 console=ttyS0,115200n8 init=/sbin/init mem=${kernelmem}; \" \\\n"
        "\t\t\"if ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then \" \\\n"
        "\t\t\t\"echo \\\"Booting kernel from UBI volume...\\\"; \" \\\n"
        "\t\t\"elif ubi part ${bootubipart} && ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then \" \\\n"
        "\t\t\t\"echo \\\"Booting kernel from UBI volume...\\\"; \" \\\n"
        "\t\t\"else \" \\\n"
        "\t\t\t\"echo \\\"UBI read kernel/dtb failed!\\\"; \" \\\n"
        "\t\t\"fi; \" \\\n"
        "\t\t\"booti ${kernel_addr_r} - ${fdt_addr_r}; fi;\\0\"\n"
    )

    new_nandargs = (
        "#define NANDARGS \\\n"
        "\t\"nandboot=\" \\\n"
        "\t\t\"mtd list; \" \\\n"
        "\t\t\"if test \\\"${mtdids}\\\" = \\\"spi-nand0=spi-nand0\\\"; then run spinandboot; else \" \\\n"
        "\t\t\"if test -z \\\"${bootubipart}\\\"; then setenv bootubipart rootfs; fi; \" \\\n"
        "\t\t\"ubi part ${bootubipart}; \" \\\n"
        "\t\t\"if ubi read ${loadaddr} u-boot-env 0x10000; then env import -c ${loadaddr} 0x10000; fi; \" \\\n"
        "\t\t\"if test -z \\\"${bootubivol}\\\"; then setenv bootubivol rofs-a; fi; \" \\\n"
        "\t\t\"if test -z \\\"${kernelname}\\\"; then setenv kernelname kernel-a; fi; \" \\\n"
        "\t\t\"if test -z \\\"${dtbname}\\\"; then setenv dtbname dtb-a; fi; \" \\\n"
        "\t\t\"echo \\\"Booting from nand (${kernelname}, ${dtbname}, ${bootubivol}) ...\\\"; \" \\\n"
        "\t\t\"setenv bootargs noinitrd ubi.mtd=${nand_ubiblock} root=ubi0:${bootubivol} rootfstype=ubifs rw rootwait=1 console=ttyS0,115200n8 init=/sbin/init mem=${kernelmem}; \" \\\n"
        "\t\t\"if ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then \" \\\n"
        "\t\t\t\"echo \\\"Booting kernel from UBI volume...\\\"; \" \\\n"
        "\t\t\"elif ubi part ${bootubipart} && ubi read ${kernel_addr_r} ${kernelname} && ubi read ${fdt_addr_r} ${dtbname}; then \" \\\n"
        "\t\t\t\"echo \\\"Booting kernel from UBI volume...\\\"; \" \\\n"
        "\t\t\"else \" \\\n"
        "\t\t\t\"echo \\\"UBI read kernel/dtb failed!\\\"; \" \\\n"
        "\t\t\"fi; \" \\\n"
        "\t\t\"booti ${kernel_addr_r} - ${fdt_addr_r}; fi;\\0\"\n"
    )

    new_mmcargs = (
        "#define MMCARGS \\\n"
        "\t\"mmcboot=\" \\\n"
        "\t\t\"if test -z \\\"${bootside}\\\"; then setenv bootside a; fi; \" \\\n"
        "\t\t\"if test -z \\\"${mmcdev}\\\"; then setenv mmcdev 0; fi; \" \\\n"
        "\t\t\"if test -z \\\"${mmc_block_prefix}\\\"; then setenv mmc_block_prefix mmcblk1; fi; \" \\\n"
        "\t\t\"if test -z \\\"${bootfile_dtb}\\\"; then setenv bootfile_dtb Image.dtb; fi; \" \\\n"
        "\t\t\"if test \\\"${bootside}\\\" = \\\"b\\\"; then \" \\\n"
        "\t\t\t\"setenv bootpart 2; setenv rofspart 5; \" \\\n"
        "\t\t\"else \" \\\n"
        "\t\t\t\"setenv bootpart 1; setenv rofspart 3; \" \\\n"
        "\t\t\"fi; \" \\\n"
        "\t\t\"if mmc dev ${mmcdev}; then \" \\\n"
        "\t\t\t\"echo \\\"Booting from MMC dev ${mmcdev} (side ${bootside}, bootpart ${bootpart}, rofspart ${rofspart}) ...\\\"; \" \\\n"
        "\t\t\t\"setenv bootargs console=ttyS0,115200 root=/dev/${mmc_block_prefix}p${rofspart} rootfstype=ext4 rw rootwait init=/sbin/init mem=${kernelmem}; \" \\\n"
        "\t\t\t\"if ext4load mmc ${mmcdev}:${bootpart} ${kernel_addr_r} fitImage; then \" \\\n"
        "\t\t\t\t\"bootm ${kernel_addr_r}; \" \\\n"
        "\t\t\t\"elif ext4load mmc ${mmcdev}:${bootpart} ${kernel_addr_r} Image && ext4load mmc ${mmcdev}:${bootpart} ${fdt_addr_r} ${bootfile_dtb}; then \" \\\n"
        "\t\t\t\t\"booti ${kernel_addr_r} - ${fdt_addr_r}; \" \\\n"
        "\t\t\t\"else \" \\\n"
        "\t\t\t\t\"echo \\\"MMC ext4load failed! Trying raw sector fallback...\\\"; \" \\\n"
        "\t\t\t\t\"setenv bootargs console=ttyS0,115200 root=/dev/${mmc_block_prefix}p1 rootfstype=ext4 rw rootwait init=/sbin/init mem=${kernelmem}; \" \\\n"
        "\t\t\t\t\"mmc read ${kernel_addr_r} 0x1800 0xf000; \" \\\n"
        "\t\t\t\t\"mmc read ${fdt_addr_r} 0x1600 0x80; \" \\\n"
        "\t\t\t\t\"booti ${kernel_addr_r} - ${fdt_addr_r}; \" \\\n"
        "\t\t\t\"fi; \" \\\n"
        "\t\t\"fi;\\0\"\n"
    )

    extra_vars = (
        "\"bootside=a\\0\" \\\n\t"
        "\"mmcdev=0\\0\" \\\n\t"
        "\"mmc_block_prefix=mmcblk1\\0\" \\\n\t"
        "\"kernelname=kernel-a\\0\" \\\n\t"
        "\"dtbname=dtb-a\\0\" \\\n\t"
        "\"bootlimit=3\\0\" \\\n\t"
        "\"bootcount=0\\0\" \\\n\t"
        "\"upgrade_available=0\\0\" \\\n\t"
        "\"altbootcmd=echo [FAILSAFE] Bootlimit exceeded! Switching active bank...; "
        "if test -n \\\"${bootside}\\\"; then "
        "if test ${bootside} = b; then setenv bootside a; else setenv bootside b; fi; fi; "
        "if test ${bootubivol} = rofs-b; then "
        "setenv bootubivol rofs-a; setenv kernelname kernel-a; setenv dtbname dtb-a; "
        "else "
        "setenv bootubivol rofs-b; setenv kernelname kernel-b; setenv dtbname dtb-b; fi; "
        "setenv upgrade_available 0; setenv bootcount 0; saveenv; "
        "if test ${boot_target} = mmc; then run mmcboot; "
        "elif test ${mtdids} = 'nand0=nand0'; then run nandboot; "
        "else run spinandboot; fi;\\0\" \\\n\t"
    )

    configs = [
        os.path.join(s_dir, "include/configs/ma35d0.h"),
        os.path.join(s_dir, "include/configs/ma35d1.h"),
        os.path.join(s_dir, "include/configs/ma35h0.h")
    ]

    for cfg_path in configs:
        if not os.path.exists(cfg_path):
            continue

        with open(cfg_path, "r") as f:
            content = f.read()

        # Increase malloc heap size from 2MB to 16MB for UBI attachment on large NAND partitions
        content = re.sub(r"#define\s+CONFIG_SYS_MALLOC_LEN\s+SZ_\w+",
                         "#define CONFIG_SYS_MALLOC_LEN\t\t\tSZ_16M", content)

        # Update MMCARGS using lambda repl for dual-bank EXT4 booting
        content = re.sub(r"#define MMCARGS\s+[\s\S]*?(?=#define BOOTENV_DEV_LEGACY_MMC)",
                         lambda m: new_mmcargs, content)

        # Update SPINANDARGS using lambda repl to prevent null byte evaluation in regex
        content = re.sub(r"#define SPINANDARGS\s+[\s\S]*?(?=#define BOOTENV_DEV_SPINAND)",
                         lambda m: new_spinandargs, content)

        # Update NANDARGS using lambda repl for pure UBI booting
        content = re.sub(r"#define NANDARGS\s+[\s\S]*?(?=#define BOOTENV_DEV_NAND)",
                         lambda m: new_nandargs, content)

        # Inject extra env variables
        content = content.replace("\"bootubivol=rootfs\\0\" \\\n",
                                  "\"bootubivol=rofs-a\\0\" \\\n\t" + extra_vars)

        # Update UBI partition block names
        content = re.sub(r"\bspinand_ubiblock=[^\\]*", "spinand_ubiblock=spinand-rootfs", content)
        content = re.sub(r"\bnand_ubiblock=[^\\]*", "nand_ubiblock=nand-rootfs", content)

        # Update bootm length and disable UBIFS distro probe (expands to empty macro)
        content = re.sub(r"CONFIG_SYS_BOOTM_LEN\s+SZ_64M", "CONFIG_SYS_BOOTM_LEN\t\t\tSZ_16M", content)
        content = re.sub(r"#define BOOT_TARGET_UBIFS\(func\).*", "#define BOOT_TARGET_UBIFS(func)", content)

        # Adjust kernel memory using string replace (avoids regex escape evaluation of \0)
        if "ma35d1" in cfg_path:
            content = content.replace("kernelmem=256M\\0", "kernelmem=512M swiotlb=1\\0")
        else:
            content = content.replace("kernelmem=256M\\0", "kernelmem=256M swiotlb=1\\0")

        if "\x00" in content:
            raise RuntimeError(f"Error: Null byte detected in patched header: {cfg_path}")

        with open(cfg_path, "w") as f:
            f.write(content)
        print(f"Successfully patched {cfg_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch-uboot-configs.py <S_DIR>")
        sys.exit(1)
    patch_configs(sys.argv[1])
