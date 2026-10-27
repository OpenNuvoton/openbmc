#!/usr/bin/env python3
#
# Script to convert MA35 DTSI NAND and SPI-NAND partitions to Pure UBI Architecture:
# - Partition 0: uboot (0x0 - 0x400000, 4MB)
# - Partition 1: rootfs (0x400000 - 0x20000000, 508MB = 0x1fc00000)
#
import os
import sys
import re
import glob

def patch_dtsi(s_dir):
    dts_dir = os.path.join(s_dir, "arch/arm64/boot/dts/nuvoton")
    dtsi_files = glob.glob(os.path.join(dts_dir, "ma35*.dtsi"))

    new_nand = """uboot@0 {
\t\t\t\t\tlabel = "nand-uboot";
\t\t\t\t\treg = <0x0 0x400000>;
\t\t\t\t};
\t\t\t\trootfs@400000 {
\t\t\t\t\tlabel = "nand-rootfs";
\t\t\t\t\treg = <0x400000 0x3fc00000>;
\t\t\t\t};"""

    new_spinand = """uboot@0 {
\t\t\t\tlabel = "spinand-uboot";
\t\t\t\treg = <0x0 0x400000>;
\t\t\t};
\t\t\trootfs@400000 {
\t\t\t\tlabel = "spinand-rootfs";
\t\t\t\treg = <0x400000 0x1fc00000>;
\t\t\t};"""

    nand_pattern = r"uboot@0\s*\{[^{}]*label\s*=\s*\"nand-uboot\"[\s\S]*?rootfs@1[cC]00000\s*\{[^{}]*\};"
    spinand_pattern = r"uboot@0\s*\{[^{}]*label\s*=\s*\"spinand-uboot\"[\s\S]*?rootfs@1[cC]00000\s*\{[^{}]*\};"

    for file_path in dtsi_files:
        with open(file_path, "r") as f:
            content = f.read()

        modified = False
        if re.search(nand_pattern, content):
            content = re.sub(nand_pattern, new_nand, content)
            modified = True
            print(f"[Pure-UBI] Patched raw NAND partitions in {os.path.basename(file_path)}")

        if re.search(spinand_pattern, content):
            content = re.sub(spinand_pattern, new_spinand, content)
            modified = True
            print(f"[Pure-UBI] Patched SPI-NAND partitions in {os.path.basename(file_path)}")

        if modified:
            with open(file_path, "w") as f:
                f.write(content)
        else:
            print(f"[Pure-UBI] No matching legacy partitions in {os.path.basename(file_path)} (already pure UBI or not applicable)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch-kernel-dtsi.py <S_DIR>")
        sys.exit(1)
    patch_dtsi(sys.argv[1])
