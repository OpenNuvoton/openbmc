# meta-evb-ma35: OpenBMC BSP Layer for Nuvoton MA35 Family

OpenBMC Board Support Package for the Nuvoton MA35 Family evaluation boards.

## Table of Contents

- [Supported Machines](#supported-machines)
- [Hardware Specifications](#hardware-specifications)
- [Features](#features)
- [Build](#build)
- [Flashing (NuWriter)](#flashing-nuwriter)
- [SPI NAND Flash Layout](#spi-nand-flash-layout)
- [Redfish API](#redfish-api)
- [Layer Structure](#layer-structure)

---

## Supported Machines

| Machine | Board | SoC |
|---------|-------|-----|
| `numaker-iot-ma35d0` | NuMaker-IoT-MA35D03F80 | MA35D0 (dual Cortex-A35 @ 650 MHz) |
| `numaker-iot-ma35d05ki1` | NuMaker-IoT-MA35D05KI1 | MA35D05K (dual Cortex-A35 @ 650 MHz) |

---

## Hardware Specifications

| Item | Detail |
|------|--------|
| RAM | 256 MB DDR3L |
| Flash | 512 MB SPI NAND |
| Kernel | Linux 6.6.93 (arm64) |
| RootFS | UBI/UBIFS on SPI NAND |
| Serial Console | ttyS0, 115200 8N1 |
| Boot Flow | SPI NAND → TF-A BL2 → BL31 → U-Boot → Linux → OpenBMC |

---

## Features

- **Redfish**: bmcweb service providing DMTF Redfish API
- **mDNS**: avahi-daemon for zero-config networking
- **SSH**: OpenSSH server
- **LED Management**: phosphor-led-manager + phosphor-led-sysfs
- **Entity Manager**: hardware inventory via entity-manager
- **Power Control**: x86-power-control (GPIO-based host power/reset)

---

## Build

```bash
# numaker-iot-ma35d05ki1
MACHINE=numaker-iot-ma35d05ki1 source setup numaker-iot-ma35d05ki1 build-ma35
bitbake nuwriter-pack

# numaker-iot-ma35d0
MACHINE=numaker-iot-ma35d0 source setup numaker-iot-ma35d0 build-ma35
bitbake nuwriter-pack
```

Output: `tmp/deploy/images/${MACHINE}/nuwriter-pack-${MACHINE}.bin`

> On subsequent builds, just `source oe-init-build-env build-ma35` to re-enter.

### Prebuilt Images

Prebuilt images are available from GitHub Actions:

[OpenBMC building → Artifacts](https://github.com/OpenNuvoton/openbmc/actions/workflows/numaker.yml)

1. Open the workflow page and select the latest successful run.
2. Scroll to the **Artifacts** section at the bottom.
3. Download the artifact for your machine (e.g. `numaker-iot-ma35d0`, `numaker-iot-ma35d05ki1`).
4. Extract the zip and flash using the batch scripts or NuWriter GUI.

---

## Flashing (NuWriter)

### Hardware Setup

1. Set the board DIP switch to **USB Boot** mode.
2. Connect the board's USB0 (Device) port to the PC with a USB cable.
3. Power on and wait for the device to be detected.

### Windows Batch Scripts

Build output includes two batch scripts for command-line flashing:

```
tmp/deploy/images/${MACHINE}/
├── install_nuwriter.bat             ← run once to set up NuWriter
└── nuwriter_program_spinand.bat     ← run to flash the board
```

**Step 1: Install NuWriter** (first time only)

```bat
install_nuwriter.bat
```

This clones [MA35D1_NuWriter](https://github.com/OpenNuvoton/MA35D1_NuWriter) and installs Python dependencies (`pyusb`, `pycryptodome`, `ecdsa`, `crcmod`, `tqdm`).

**Step 2: Program SPI NAND**

```bat
nuwriter_program_spinand.bat
```

The script performs:
1. DDR initialization (loads DDR training image)
2. Erase entire SPI NAND
3. Program `nuwriter-pack-${MACHINE}.bin` to flash

After completion, set DIP switch back to **SPI NAND Boot** and power on.

> **Prerequisites**: Python 3, Git, and the board in USB Boot mode. Place the batch scripts in the same directory as `nuwriter-pack-${MACHINE}.bin`.

### NuWriter GUI (Alternative)

1. Open `NuWriter.exe` → Storage Type: **SPI NAND**.
2. Click **Erase** → check **Erase All** → execute.
3. Set Image Type to **Pack** → browse `nuwriter-pack-${MACHINE}.bin`.
4. Click **Burn** and wait.
5. Power off → set DIP switch back to **SPI NAND Boot** → power on.

### Verifying Boot

Connect serial console (115200 8N1):

```
NOTICE:  BL2: v2.3 ...
NOTICE:  BL31: v2.3 ...
U-Boot 2020.07 ...
[    0.000000] Linux version 6.6.93 ...
...
numaker-iot-ma35d0 login:
```

Default login: `root` (Password: 0penBmc).

---

## SPI NAND Flash Layout

Total: 512 MB (`0x0`–`0x10000000`)

| MTD | Label | Address Range | Size | Contents |
|-----|-------|---------------|------|----------|
| mtd0 | `spinand-uboot` | `0x000000`–`0x300000` | 3 MB | Header + BL2 + FIP (BL31+U-Boot) |
| mtd1 | `spinand-uboot-env` | `0x300000`–`0x3C0000` | 768 KB | U-Boot environment |
| mtd2 | `spinand-device-tree` | `0x3C0000`–`0x400000` | 256 KB | Linux DTB |
| mtd3 | `spinand-kernel` | `0x400000`–`0x1C00000` | 24 MB | Linux kernel (Image) |
| mtd4 | `spinand-rootfs` | `0x1C00000`–`0x10000000` | 228 MB | UBI volume (UBIFS rootfs) |

---

## Redfish API

BMC is accessible via mDNS hostname: `${MACHINE}.local`

For power control (wiring, GPIO pin assignment, Redfish/D-Bus commands), see:
- [doc/x86-power-control/numaker-iot-ma35d0.md](../../doc/x86-power-control/numaker-iot-ma35d0.md)
- [doc/x86-power-control/numaker-iot-ma35d05ki1.md](../../doc/x86-power-control/numaker-iot-ma35d05ki1.md)

### Quick Examples

```bash
# Service Root
curl -k -s https://${MACHINE}.local/redfish/v1/

# Toggle Chassis Identify LED
curl -k -s -u root:0penBmc -X PATCH \
  https://${MACHINE}.local/redfish/v1/Chassis/system \
  -H "Content-Type: application/json" \
  -d '{"LocationIndicatorActive": true}'

# SSH access
ssh root@${MACHINE}.local
```

---

## Layer Structure

```
meta-evb-ma35/
├── conf/
│   ├── layer.conf
│   ├── machine/
│   │   ├── include/ma35-common.inc
│   │   ├── numaker-iot-ma35d0.conf
│   │   └── numaker-iot-ma35d05ki1.conf
│   └── templates/default/
│       ├── bblayers.conf.sample
│       └── local.conf.sample
├── recipes-bsp/
│   ├── tf-a/
│   │   ├── tf-a-ma35.inc
│   │   ├── tf-a-ma35_2.3.bb
│   │   └── files/ (DDR headers)
│   └── u-boot/
│       ├── u-boot-ma35.inc
│       └── u-boot-ma35_2020.07.bb
├── recipes-core/systemd/
│   ├── systemd_%.bbappend
│   └── systemd-serialgetty.bbappend
├── recipes-devtools/python/
│   ├── nuwriter-pack.inc
│   ├── nuwriter-pack_1.0.bb
│   ├── python3-nuwriter-native_0.90.bb
│   └── files/ (header-spinand.json, pack-spinand.json, batch scripts)
├── recipes-kernel/linux/
│   ├── linux-ma35.inc
│   ├── linux-ma35_6.6.93.bb
│   ├── linux-ma35/ (openbmc.cfg)
│   └── files/ (defconfigs, DTS, patches)
├── recipes-nuvoton/packagegroups/
│   └── packagegroup-ma35-apps.bb
├── recipes-phosphor/
│   ├── entity-manager/
│   │   ├── entity-manager_%.bbappend
│   │   └── entity-manager/ (per-machine JSON configs)
│   ├── images/obmc-phosphor-image.bbappend
│   ├── leds/ (led-group-config.json)
│   └── packagegroups/packagegroup-obmc-apps.bbappend
└── recipes-x86/chassis/
    ├── x86-power-control_%.bbappend
    └── x86-power-control/power-config-host0.json
```
