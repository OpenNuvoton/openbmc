# meta-evb-ma35d0: OpenBMC BSP Layer for Nuvoton MA35D0

OpenBMC Board Support Package for the **Nuvoton NuMaker-IoT-MA35D06F80** evaluation board.

## Table of Contents

- [Hardware Specifications](#hardware-specifications)
- [Features](#features)
- [Build](#build)
- [Flashing (NuWriter)](#flashing-nuwriter)
- [SPI NAND Flash Layout](#spi-nand-flash-layout)
- [GPIO LEDs](#gpio-leds)
- [Redfish API](#redfish-api)
- [Layer Structure](#layer-structure)

---

## Hardware Specifications

| Item | Detail |
|------|--------|
| SoC | MA35D0 (dual Cortex-A35 @ 650 MHz) |
| RAM | 256 MB DDR3L |
| Flash | 512 MB SPI NAND |
| Kernel | Linux 6.6.93 (arm64) |
| RootFS | UBI/UBIFS on SPI NAND |
| Serial Console | ttyS0, 115200 8N1 |
| Boot Flow | SPI NAND → TF-A BL2 → BL31 → U-Boot → Linux → OpenBMC |

---

## Features

- **Redfish**: bmcweb service providing DMTF Redfish API
- **LED Management**: phosphor-led-manager (enclosure identify, power)
- **Entity Manager**: hardware inventory via entity-manager

---

## Build

```bash
# Clone
git clone -b numaker https://github.com/OpenNuvoton/openbmc.git
cd openbmc

# First-time setup
TEMPLATECONF=meta-numaker/meta-evb-ma35d0/conf/templates/default \
  source oe-init-build-env build-ma35d0

# Build (generates pack.bin automatically)
bitbake nuwriter-ma35d0-pack
```

Output: `tmp/deploy/images/numaker-iot-ma35d0/pack/pack.bin`

> On subsequent builds, just `source oe-init-build-env build-ma35d0` to re-enter.

To build only the OpenBMC image (without NuWriter pack):

```bash
bitbake obmc-phosphor-image
```

---

## Flashing (NuWriter)

Tool download: [NuWriter (Windows)](https://github.com/OpenNuvoton/MA35D1_NuWriter)

### Hardware Setup

1. Set the board DIP switch to **USB Boot** mode.
2. Connect the board's USB port to the PC with a USB cable.
3. Power on and wait for NuWriter to detect the device.

### One-Key Flash (Recommended)

Writes all components at once (header + BL2 + FIP + DTB + kernel + rootfs):

1. Run the provided batch script:
   ```
   nuwriter_program_spinand.bat
   ```
   This performs DDR init, full SPI NAND erase, and programs `pack.bin`.
2. Power off → set DIP switch back to **SPI NAND Boot** → power on.

### Individual Component

| Component | File | Start Address |
|-----------|------|---------------|
| Boot Header | `conv/header.bin` | `0x000000` |
| BL2 DTB | `bl2-ma35d0.dtb` | `0x0C0000` |
| BL2 | `bl2-ma35d0.bin` | `0x0E0000` |
| FIP (BL31 + U-Boot) | `fip.bin` | `0x100000` |
| Kernel DTB | `Image.dtb` | `0x3C0000` |
| Kernel | `Image` | `0x400000` |
| RootFS | `obmc-phosphor-image.ubi` | `0x1C00000` |

```bash
# Example: flash only the kernel
python3 nuwriter.py -write spinand 0x400000 Image

# Example: flash only the rootfs
python3 nuwriter.py -write spinand 0x1C00000 obmc-phosphor-image.ubi
```

> **Note:** When flashing rootfs individually, erase the UBI region first:
> `python3 nuwriter.py -e spinand all`

### Verifying Boot

Connect serial console (115200 8N1):

```
MA35D0 TF-A: BL2 ...
MA35D0 TF-A: BL31 ...
U-Boot 2020.07 ...
Loading kernel ...
[    0.000000] Linux version 6.6.93 ...
[    1.xxx] UBIFS: mounted UBI device 0
...
numaker-iot-ma35d0 login:
```

Default login: `root` (no password). Set password via Redfish after first login.

---

## SPI NAND Flash Layout

Total: 512 MB

| MTD | Label | Address Range | Size | Contents |
|-----|-------|---------------|------|----------|
| mtd0 | `spinand-uboot` | `0x000000`–`0x300000` | 3 MB | Boot header + BL2 + FIP |
| mtd1 | `spinand-uboot-env` | `0x300000`–`0x3C0000` | 768 KB | U-Boot environment |
| mtd2 | `spinand-device-tree` | `0x3C0000`–`0x400000` | 256 KB | Linux DTB |
| mtd3 | `spinand-kernel` | `0x400000`–`0x1C00000` | 24 MB | Linux kernel (Image) |
| mtd4 | `spinand-rootfs` | `0x1C00000`–end | ~484 MB | UBI volume (UBIFS rootfs) |

---

## GPIO LEDs

| LED | Function | sysfs |
|-----|----------|-------|
| front_id | Enclosure Identify (Blink) | `/sys/class/leds/front_id/brightness` |
| power | Power On indicator | `/sys/class/leds/power/brightness` |

---

## Redfish API

BMC IP is obtained via DHCP. Check your DHCP server or serial console for the assigned address.

### Quick Examples

```bash
# Service Root
curl -k -s https://<BMC_IP>/redfish/v1/

# Query host power state
curl -k -s -u root:0penBmc \
  https://<BMC_IP>/redfish/v1/Systems/system | jq '.PowerState'

# Toggle Chassis Identify LED
curl -k -s -u root:0penBmc -X PATCH \
  https://<BMC_IP>/redfish/v1/Chassis/system \
  -H "Content-Type: application/json" \
  -d '{"LocationIndicatorActive": true}'
```

### Verified Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/redfish/v1/` | GET | Service Root |
| `/redfish/v1/Chassis/system` | GET/PATCH | Chassis info, LocationIndicatorActive |
| `/redfish/v1/Systems/system` | GET | Host power state, health |
| `/redfish/v1/Managers/bmc` | GET | BMC manager status |

---

## Layer Structure

```
meta-evb-ma35d0/
├── conf/
│   ├── layer.conf
│   ├── machine/
│   │   ├── include/ma35d0.inc
│   │   └── numaker-iot-ma35d0.conf
│   └── templates/default/
│       ├── bblayers.conf.sample
│       └── local.conf.sample
├── recipes-bsp/
│   ├── tf-a/
│   │   ├── tf-a-ma35d0_2.3.bb
│   │   └── files/ (DDR header)
│   └── u-boot/
│       └── u-boot-ma35d0_2020.07.bb
├── recipes-core/systemd/
│   └── systemd-serialgetty.bbappend
├── recipes-devtools/python/
│   ├── nuwriter-ma35d0-pack_1.0.bb
│   ├── python3-nuwriter-native_0.90.bb
│   └── files/ (header-spinand.json, pack-spinand.json, batch scripts)
├── recipes-kernel/linux/
│   ├── linux-ma35d0_6.6.93.bb
│   ├── linux-ma35d0/openbmc.cfg
│   └── files/ (defconfig, DTS, DMA patch)
├── recipes-nuvoton/packagegroups/
│   └── packagegroup-ma35d0-apps.bb
└── recipes-phosphor/
    ├── entity-manager/ (numaker-iot-ma35d0.json)
    ├── images/obmc-phosphor-image.bbappend
    ├── leds/ (led-group-config.json)
    └── packagegroups/packagegroup-obmc-apps.bbappend
```


