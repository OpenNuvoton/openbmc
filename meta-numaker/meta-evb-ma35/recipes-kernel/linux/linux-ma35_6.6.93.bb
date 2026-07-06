# Copyright 2025 Nuvoton
# Released under the MIT license (see COPYING.MIT for the terms)

SUMMARY = "Linux Kernel for Nuvoton MA35 Series"
DESCRIPTION = "Linux Kernel provided and supported by Nuvoton for MA35 SoC family (OpenBMC)"

require linux-ma35.inc

LOCALVERSION = "${MA35_LOCALVERSION}"

COMPATIBLE_MACHINE = "(ma35d0|ma35d05k)"
