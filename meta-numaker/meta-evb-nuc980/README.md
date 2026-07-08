# meta-evb-nuc980: OpenBMC BSP Layer for NuMaker-IoT-NUC980G2

OpenBMC Board Support Package for the **Nuvoton NuMaker-IoT-NUC980G2** board.

## Table of Contents

- [Hardware Specifications](#hardware-specifications)
- [Features](#features)
- [Build](#build)
- [Flashing (NuWriter)](#flashing-nuwriter)
- [SPI NAND Flash Layout](#spi-nand-flash-layout)
- [Redfish API](#redfish-api)
- [Layer Structure](#layer-structure)

---

## Hardware Specifications

| Item | Detail |
|------|--------|
| SoC | NUC980DK71YC (ARM926EJ-S @ 300 MHz) |
| RAM | 128 MB DDR2 |
| Flash | 128 MB SPI NAND (Winbond W25N01GV) |
| Kernel | Linux 6.6.93 |
| RootFS | UBI/UBIFS on SPI NAND |
| Serial Console | ttyS0, 115200 8N1 |

---

## Features

- **Redfish**: bmcweb service providing DMTF Redfish API
- **mDNS**: avahi-daemon for zero-config networking (`numaker-iot-nuc980g2.local`)
- **SSH**: dropbear (ed25519 + ecdsa only, no RSA for fast boot)
- **LED Management**: phosphor-led-manager + phosphor-led-sysfs
- **Entity Manager**: hardware inventory via entity-manager
- **Power Control**: x86-power-control (GPIO-based host power/reset)

---

## Build

```bash
# Clone
git clone -b numaker https://github.com/OpenNuvoton/openbmc.git
cd openbmc

# First-time setup
MACHINE=numaker-iot-nuc980g2 source setup numaker-iot-nuc980g2 build-nuc980

# Build (generates nuwriter_pack.bin automatically)
bitbake nuwriter-pack
```

Output: `tmp/deploy/images/numaker-iot-nuc980g2/nuwriter-pack.bin`

> On subsequent builds, just `source oe-init-build-env build-nuc980` to re-enter.

### Prebuilt Images

Prebuilt images are available from GitHub Actions:

[OpenBMC building → Artifacts](https://github.com/OpenNuvoton/openbmc/actions/workflows/numaker.yml)

1. Open the workflow page and select the latest successful run.
2. Scroll to the **Artifacts** section at the bottom.
3. Download the artifact for `numaker-iot-nuc980g2`.
4. Extract the zip and flash using NuWriter.

---

## Flashing (NuWriter)

Tool download: [NuWriter (Windows)](https://github.com/OpenNuvoton/NUC980_NuWriter)

### Hardware Setup

1. Set the board DIP switch to **USB Boot** mode.
2. Connect the board's USB0 (Device) port to the PC with a USB cable.
3. Power on and wait for NuWriter to detect the device.

### One-Key Pack (Recommended)

Writes all components at once (SPL + env + U-Boot + DTB + kernel + rootfs):

1. Open `NuWriter.exe` → Storage Type: **SPI NAND**.
2. Click **Erase** → check **Erase All** → execute.
3. Set Image Type to **Pack** → browse `nuwriter-pack.bin`.
4. Click **Burn** and wait (~2-3 minutes).
5. Power off → set DIP switch back to **SPI NAND Boot** → power on.

### Individual Component

| Component | File | Image Type | Start Address |
|-----------|------|------------|---------------|
| SPL | `u-boot-spl.bin` | Loader | `0x0` |
| U-Boot Env | `uboot-env.txt` | Environment | `0x80000` |
| U-Boot | `u-boot.bin` | Data | `0x100000` |
| DTB | `nuc980-iot-128m-bmc.dtb` | Data | `0x180000` |
| Kernel | `uImage` | Data | `0x200000` |
| RootFS | `obmc-phosphor-image-*.ubi` | Data | `0x800000` |

> **Note:** Before flashing rootfs individually, erase the region (`0x800000`–`0x8000000`) first to avoid UBI attach failures.

### Verifying Boot

Connect serial console (115200 8N1):

```
U-Boot SPL 2016.11 ...
U-Boot 2016.11 ...
Loading kernel from NAND 0x200000...
[    0.000000] Linux version 6.6.93 ...
[    1.xxx] UBIFS (ubi0:0): mounted on MTD3
...
numaker-iot-nuc980g2 login:
```

Default login: `root` (Password: 0penBmc).

---

## SPI NAND Flash Layout

Total: 128 MB (`0x0`–`0x8000000`)

| MTD | Label | Address Range | Size | Contents |
|-----|-------|---------------|------|----------|
| mtd0 | `u-boot` | `0x000000`–`0x100000` | 1 MB | SPL + U-Boot env |
| mtd1 | `u-boot-env` | `0x100000`–`0x180000` | 512 KB | U-Boot |
| mtd2 | `kernel` | `0x180000`–`0x800000` | 6.5 MB | DTB + uImage |
| mtd3 | `rofs` | `0x800000`–`0x3800000` | 48 MB | UBI volume (UBIFS rootfs) |
| mtd4 | `rwfs` | `0x3800000`–`0x8000000` | 72 MB | UBI volume (UBIFS rwfs) |

---

## Redfish API

BMC is accessible via mDNS hostname: `numaker-iot-nuc980g2.local`

For power control (wiring, GPIO pin assignment, Redfish/D-Bus commands), see [doc/x86-power-control/numaker-iot-nuc980g2.md](../../doc/x86-power-control/numaker-iot-nuc980g2.md).

### Quick Examples

```bash
# Service Root
curl -k -s https://numaker-iot-nuc980g2.local/redfish/v1/

# Toggle Chassis Identify LED
curl -k -s -u root:0penBmc -X PATCH \
  https://numaker-iot-nuc980g2.local/redfish/v1/Chassis/system \
  -H "Content-Type: application/json" \
  -d '{"LocationIndicatorActive": true}'

# SSH access
ssh root@numaker-iot-nuc980g2.local
```

---

## Layer Structure

```
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
