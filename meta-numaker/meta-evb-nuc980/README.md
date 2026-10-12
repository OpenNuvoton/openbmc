# meta-evb-nuc980: OpenBMC BSP Layer for NuMaker-IoT-NUC980G2

OpenBMC Board Support Package (BSP) layer for the **Nuvoton NuMaker-IoT-NUC980G2** evaluation board.

## Table of Contents

- [Supported Machine](#supported-machine)
- [Hardware Specifications](#hardware-specifications)
- [Layer Features](#layer-features)
- [Quick Build](#quick-build)
- [SPI NAND Flash Layout](#spi-nand-flash-layout)
- [Board Documentation & Feature Guides](#board-documentation--feature-guides)
- [Layer Structure](#layer-structure)

---

## Supported Machine

| Machine | Board | SoC | Board Documentation |
| :--- | :--- | :--- | :--- |
| `numaker-iot-nuc980g2` | NuMaker-IoT-NUC980G2 | NUC980DK71YC (ARM926EJ-S @ 300 MHz) | [User & Operation Guide](../doc/numaker-iot-nuc980g2/README.md) |

---

## Hardware Specifications

| Item | Detail |
| :--- | :--- |
| **SoC** | NUC980DK71YC (ARM926EJ-S @ 300 MHz) |
| **RAM** | 128 MB DDR2 (stacked in MCP) |
| **Flash** | 128 MB SPI NAND (Winbond W25N01GV) |
| **Kernel** | Linux 6.6.93 (armv5te) |
| **RootFS** | UBI/UBIFS on SPI NAND |
| **Debug Console** | ttyS0, 115200 8N1 |

---

## Layer Features

- **Redfish & REST API**: `bmcweb` providing standard DMTF Redfish API (`/redfish/v1/`), telemetry, chassis/system control, sensor readings, and WebUI hosting.
- **Zero-Config Networking**: `avahi-daemon` (mDNS as `numaker-iot-nuc980g2.local`).
- **Remote Access**: Dropbear SSH server (ed25519 + ecdsa only for optimized boot time).
- **LED Management**: `phosphor-led-manager` + `phosphor-led-sysfs` with group and location indicator controls.
- **Entity Manager & Sensor Config**: Dynamic hardware inventory and configuration via `entity-manager` JSON schemas.
- **Host Power Control**: `x86-power-control` daemon providing GPIO-based host power on, power off, power cycle, and reset state machine management.

---

## Quick Build

```bash
# Clone
git clone -b numaker https://github.com/OpenNuvoton/openbmc.git
cd openbmc

# Initialize build environment
MACHINE=numaker-iot-nuc980g2 source setup numaker-iot-nuc980g2 build-nuc980

# Build OpenBMC NuWriter Pack
bitbake nuwriter-pack
```

Output: `build-nuc980/tmp/deploy/images/numaker-iot-nuc980g2/nuwriter-pack.bin`

> [!TIP]
> For complete step-by-step build instructions (including the recommended pre-configured Docker container), DIP switch settings, NuWriter flashing, and boot verification, please refer to the dedicated board guide:
> - [NuMaker-IoT-NUC980G2 User & Operation Guide](../doc/numaker-iot-nuc980g2/README.md)
> - [Docker Build Environment Guide](../doc/docker/README.md)

---

## SPI NAND Flash Layout

Total: 128 MB (`0x0`–`0x8000000`)

| MTD | Label | Address Range | Size | Contents |
| :--- | :--- | :--- | :--- | :--- |
| `mtd0` | `u-boot` | `0x000000`–`0x100000` | 1 MB | SPL + U-Boot env |
| `mtd1` | `u-boot-env` | `0x100000`–`0x180000` | 512 KB | U-Boot |
| `mtd2` | `kernel` | `0x180000`–`0x800000` | 6.5 MB | DTB + uImage |
| `mtd3` | `rofs` | `0x800000`–`0x3800000` | 48 MB | UBI volume (UBIFS rootfs) |
| `mtd4` | `rwfs` | `0x3800000`–`0x8000000` | 72 MB | UBI volume (UBIFS rwfs) |

---

## Board Documentation & Feature Guides

The following documents provide complete instructions and test suites for `numaker-iot-nuc980g2`:

- **Main Board Guide**: [NuMaker-IoT-NUC980G2 User & Operation Guide](../doc/numaker-iot-nuc980g2/README.md)
- **Redfish Test Suite**: [test-redfish.md](../doc/numaker-iot-nuc980g2/test-redfish.md) (Automated script: `test-redfish.sh`)
- **Host Power Control**: [test-power-control.md](../doc/numaker-iot-nuc980g2/test-power-control.md)

---

## Layer Structure

```text
meta-evb-nuc980/
├── conf/
│   ├── layer.conf
│   ├── machine/
│   │   ├── include/nuc980.inc
│   │   └── numaker-iot-nuc980g2.conf
│   └── templates/default/
│       ├── bblayers.conf.sample
│       └── local.conf.sample
├── recipes-bsp/u-boot/
│   └── u-boot-nuc980_git.bb
├── recipes-core/
│   ├── dropbear/
│   │   ├── dropbear_%.bbappend
│   │   └── dropbear/ (dropbearkey.service, dropbear@.service)
│   ├── systemd/
│   │   ├── phosphor-systemd-policy.bbappend
│   │   ├── systemd_%.bbappend
│   │   └── systemd-serialgetty.bbappend
│   └── volatile-binds/
│       └── volatile-binds.bbappend
├── recipes-devtools/python/
│   ├── nuwriter-pack_1.0.bb
│   └── files/ (NUC980DK71YC.ini, nuwriter_pack.py, uboot-env.txt)
├── recipes-kernel/linux/
│   ├── linux-nuc980_6.6.93.bb
│   └── linux-nuc980/ (DTS patch, kernel configs)
├── recipes-nuvoton/packagegroups/
│   └── packagegroup-nuc980-apps.bb
├── recipes-phosphor/
│   ├── entity-manager/ (nuc980-evb.json, LED association patch)
│   ├── images/obmc-phosphor-image.bbappend
│   ├── interfaces/bmcweb_%.bbappend
│   ├── leds/ (led-group-config.json, sysfs retry patch)
│   └── packagegroups/packagegroup-obmc-apps.bbappend
└── recipes-x86/chassis/
    ├── x86-power-control_%.bbappend
    └── x86-power-control/power-config-host0.json
```
