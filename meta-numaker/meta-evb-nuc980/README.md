# meta-evb-nuc980: OpenBMC BSP Layer for Nuvoton NUC980 IoT-G2

OpenBMC Board Support Package for the **Nuvoton NuMaker IoT NUC980G2** board.

## Table of Contents

- [Hardware Specifications](#hardware-specifications)
- [Features](#features)
- [Build](#build)
- [Flashing (NuWriter)](#flashing-nuwriter)
- [SPI NAND Flash Layout](#spi-nand-flash-layout)
- [GPIO](#gpio)
- [Power Control](#power-control)
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
- **LED Management**: phosphor-led-manager + phosphor-led-sysfs
- **Entity Manager**: hardware inventory via entity-manager
- **Power Control**: x86-power-control (GPIO-based host power/reset)
- **Health Monitoring**: phosphor-health-monitor (BMC health metrics)

---

## Build

```bash
# Clone
git clone -b numaker https://github.com/OpenNuvoton/openbmc.git
cd openbmc

# First-time setup
TEMPLATECONF=meta-numaker/meta-evb-nuc980/conf/templates/default \
  source oe-init-build-env build-nuc980

# Build (generates nuwriter_pack.bin automatically)
bitbake nuwriter-nuc980-pack
```

Output: `tmp/deploy/images/numaker-iot-nuc980g2/nuwriter_pack.bin`

> On subsequent builds, just `source oe-init-build-env build-nuc980` to re-enter.

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
3. Set Image Type to **Pack** → browse `nuwriter_pack.bin`.
4. Click **Burn** and wait (~2-3 minutes).
5. Power off → set DIP switch back to **SPI NAND Boot** → power on.

### Individual Component

| Component | File | Image Type | Start Address |
|-----------|------|------------|---------------|
| SPL | `u-boot-spl.bin` | Loader | `0x0` |
| U-Boot Env | `uboot-env.txt` | Environment | `0x80000` |
| U-Boot | `u-boot.bin` | Data | `0x100000` |
| DTB | `nuc980-iot-g2-v1.0.dtb` | Data | `0x180000` |
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

Default login: `root` (no password). Set password via Redfish after first login.

---

## SPI NAND Flash Layout

Total: 128 MB (`0x0`–`0x8000000`)

| MTD | Label | Address Range | Size | Contents |
|-----|-------|---------------|------|----------|
| mtd0 | `u-boot` | `0x000000`–`0x100000` | 1 MB | SPL + U-Boot |
| mtd1 | `u-boot-env` | `0x100000`–`0x180000` | 512 KB | U-Boot environment |
| mtd2 | `kernel` | `0x180000`–`0x800000` | 6.5 MB | DTB + uImage |
| mtd3 | `rofs` | `0x800000`–`0x3800000` | 48 MB | UBI volume (UBIFS rootfs) |
| mtd4 | `rwfs` | `0x3800000`–`0x8000000` | 72 MB | UBI volume (UBIFS rwfs) |

---

## GPIO

### LED

| LED | GPIO | Active | sysfs |
|-----|------|--------|-------|
| front_id | PB13 | Low | `/sys/class/leds/front_id/brightness` |
| power | PG15 | Low | `/sys/class/leds/power/brightness` |

---

## Power Control

Host power control is implemented via `x86-power-control` daemon using GPIO.

### Pin Assignment

| Signal | Direction | GPIO | Function |
|--------|-----------|------|----------|
| `POWER_OUT` | Output | PD12 (108) | Power button (200ms=On, 4s=ForceOff) |
| `RESET_OUT` | Output | PD13 (109) | Reset button (500ms pulse) |
| `PS_PWROK` | Input | PF9 (169) | Host PSU Power Good |

### Wiring

```
NUC980 (BMC)                   Host Motherboard
─────────────                  ────────────────
PD12 (POWER_OUT)  ─────────── PWR_BTN# (power button header)
PD13 (RESET_OUT)  ─────────── RST_BTN# (reset button header)
PF9  (PS_PWROK)   ◄────────── PWROK (ATX PSU / VRM output)
GND ──────────────────────── GND (common ground)
```

> NUC980 GPIO is 3.3V. POWER_OUT/RESET_OUT are active-low (pulled low to trigger). PF9 requires a 10kΩ pull-down when no host is connected.

### Supported Operations

| Operation | Redfish ResetType | Pulse Pin | Duration |
|-----------|-------------------|-----------|----------|
| Power On | `On` | PD12 | 200ms |
| Graceful Shutdown | `GracefulShutdown` | PD12 | 200ms (then 4s after 300s timeout) |
| Force Off | `ForceOff` | PD12 | 4000ms |
| Force Restart | `ForceRestart` | PD13 | 500ms |

See [PowerControl.md](PowerControl.md) for detailed wiring, configuration, and verification steps.

---

## Redfish API

BMC IP is obtained via DHCP (e.g. `192.168.0.57`). Check your DHCP server or serial console for the assigned address.

### Quick Examples

```bash
# Service Root
curl -k -s https://192.168.0.57/redfish/v1/

# Query host power state
curl -k -s -u root:0penBmc \
  https://192.168.0.57/redfish/v1/Systems/system | jq '.PowerState'

# Power On
curl -k -s -u root:0penBmc -X POST \
  https://192.168.0.57/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" -d '{"ResetType": "On"}'

# Force Off
curl -k -s -u root:0penBmc -X POST \
  https://192.168.0.57/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" -d '{"ResetType": "ForceOff"}'

# Toggle Chassis Identify LED
curl -k -s -u root:0penBmc -X PATCH \
  https://192.168.0.57/redfish/v1/Chassis/system \
  -H "Content-Type: application/json" \
  -d '{"LocationIndicatorActive": true}'
```

### Verified Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/redfish/v1/` | GET | Service Root |
| `/redfish/v1/Chassis/system` | GET/PATCH | Chassis info, LocationIndicatorActive |
| `/redfish/v1/Systems/system` | GET | Host power state, health |
| `/redfish/v1/Systems/system/Actions/ComputerSystem.Reset` | POST | Power control actions |
| `/redfish/v1/Managers/bmc` | GET | BMC manager status |
| `/redfish/v1/Chassis/system/Thermal` | GET | Thermal subsystem |
| `/redfish/v1/Chassis/system/Power` | GET | Power subsystem |
| `/redfish/v1/Chassis/system/Sensors` | GET | Sensor collection |

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
│   ├── systemd/
│   │   ├── phosphor-systemd-policy.bbappend
│   │   ├── systemd_%.bbappend
│   │   └── systemd-serialgetty.bbappend
│   └── volatile-binds/
│       └── volatile-binds.bbappend
├── recipes-devtools/python/
│   ├── nuwriter-nuc980-pack_1.0.bb
│   └── files/ (NUC980DK71YC.ini, nuwriter_pack.py, uboot-env.txt)
├── recipes-kernel/linux/
│   ├── linux-nuc980_6.6.93.bb
│   └── linux-nuc980/ (DTS patch, kernel configs)
├── recipes-nuvoton/packagegroups/
│   └── packagegroup-nuc980-apps.bb
├── recipes-phosphor/
│   ├── entity-manager/ (nuc980-evb.json, LED association patch)
│   ├── health/ (bmc_health_config.json)
│   ├── images/obmc-phosphor-image.bbappend
│   ├── interfaces/bmcweb_%.bbappend
│   ├── leds/ (led-group-config.json, sysfs retry patch)
│   ├── packagegroups/packagegroup-obmc-apps.bbappend
│   └── state/phosphor-state-manager_%.bbappend
└── recipes-x86/chassis/
    ├── x86-power-control_%.bbappend
    └── x86-power-control/power-config-host0.json
```
