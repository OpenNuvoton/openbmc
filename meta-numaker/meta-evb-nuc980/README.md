# meta-evb-nuc980: OpenBMC BSP Layer for NuMaker-IoT-NUC980G2

OpenBMC BSP layer for the Nuvoton NuMaker-IoT-NUC980G2 evaluation board (ARM926EJ-S).

## Table of Contents

- [Layer Features](#layer-features)
- [SPI-NAND Flash Layout](#spi-nand-flash-layout)
- [Board Documentation & Test Guides](#board-documentation--test-guides)
- [Layer Structure](#layer-structure)

---

## Layer Features

- **Redfish API**: `bmcweb` (`/redfish/v1/`) for chassis/system control, sensor readings, and user management (`webui-vue` is omitted to fit the 128 MB RAM budget).
- **SSH & Network Discovery**: Dropbear SSH server (configured with `ed25519` and `ecdsa` keys only to reduce first-boot key generation time on ARM926EJ-S) and `avahi-daemon` (`numaker-iot-nuc980g2.local`).
- **Host Power Control**: GPIO-based host power state machine (`POWER_OUT`, `RESET_OUT`, `PS_PWROK`, `POST_COMPLETE`) via `x86-power-control`.
- **Hardware Inventory & LEDs**: `entity-manager` (`nuc980-evb.json`) and `phosphor-led-manager` + `phosphor-led-sysfs` (`front_id` on PB13, `power` on PG15).

---

## SPI-NAND Flash Layout

Total capacity: 128 MB (`0x0000000`–`0x8000000`)

| MTD | Label | Address Range | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `mtd0` | `u-boot` | `0x0000000`–`0x0100000` | 1 MB | U-Boot SPL (`0x0`) + U-Boot environment (`0x80000`) |
| `mtd1` | `u-boot-env` | `0x0100000`–`0x0180000` | 512 KB | U-Boot proper (`u-boot.bin`) |
| `mtd2` | `kernel` | `0x0180000`–`0x0800000` | 6.5 MB | Device tree (`0x180000`) + Kernel `uImage` (`0x200000`) |
| `mtd3` | `rofs` | `0x0800000`–`0x3800000` | 48 MB | Read-only rootfs UBI volume (`ubifs`) |
| `mtd4` | `rwfs` | `0x3800000`–`0x8000000` | 72 MB | Persistent overlay UBI volume (`/var`) |

---

## Board Documentation & Test Guides

| Machine | Board Guide | Redfish API | Power Control |
| :--- | :---: | :---: | :---: |
| **NUC980G2** | [Guide](../doc/numaker-iot-nuc980g2/README.md) | [Test](../doc/numaker-iot-nuc980g2/test-redfish.md) | [Test](../doc/numaker-iot-nuc980g2/test-power-control.md) |

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
│   └── files/ (NUC980DK71YC.ini, nuwriter_pack.py, nuwriter_unpack.py, uboot-env.txt)
├── recipes-kernel/linux/
│   ├── linux-nuc980_6.6.93.bb
│   └── linux-nuc980/ (nuc980-iot-128m-bmc.dts, kernel defconfig & fragments)
├── recipes-nuvoton/packagegroups/
│   └── packagegroup-nuc980-apps.bb
├── recipes-phosphor/
│   ├── entity-manager/
│   │   ├── entity-manager_%.bbappend
│   │   └── entity-manager/ (nuc980-evb.json, LED association patch)
│   ├── images/obmc-phosphor-image.bbappend
│   ├── interfaces/bmcweb_%.bbappend
│   ├── leds/
│   │   ├── phosphor-led-manager_%.bbappend
│   │   ├── phosphor-led-sysfs_%.bbappend
│   │   └── phosphor-led-manager/led-group-config.json
│   └── packagegroups/packagegroup-obmc-apps.bbappend
└── recipes-x86/chassis/
    ├── x86-power-control_%.bbappend
    └── x86-power-control/power-config-host0.json
```
