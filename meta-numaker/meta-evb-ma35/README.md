# meta-evb-ma35: OpenBMC BSP Layer for Nuvoton MA35 Family

OpenBMC BSP layer for Nuvoton MA35 evaluation boards (dual Arm Cortex-A35).

## Table of Contents

- [Layer Features](#layer-features)
- [Storage Layout](#storage-layout)
- [Board Documentation & Test Guides](#board-documentation--test-guides)
- [Layer Structure](#layer-structure)

---

## Layer Features

- **Redfish & WebUI**: `bmcweb` (`/redfish/v1/`) and `webui-vue` with real-time sensor polling chart.
- **Redfish Firmware Update (OTA)**: Dual-bank A/B firmware update via `bmcweb` multipart direct-to-disk streaming (`/redfish/v1/UpdateService/update`) and `phosphor-software-manager`, supporting anti-rollback checks and U-Boot boot-target switching across SPI-NAND, Raw NAND, and SD/eMMC.
- **User & Access Management**: `phosphor-user-manager` supporting local accounts, RBAC (`Administrator`, `Operator`, `ReadOnly`), account lockout, and password policies.
- **SoC Thermal Sensor (`ma35-soc-temp`)**: Polls the on-die TSEN thermal zone via sysfs and exports `/xyz/openbmc_project/sensors/temperature/cpu_thermal` on D-Bus (Warning: `95°C`, Critical: `105°C`).
- **Serial-Over-LAN (`obmc-console`)**: Routes host UART (`ttyS4` / `ttyS6` / `ttyS10`) to WebUI WebSocket terminal and SSH port 2200.
- **Industrial Interfaces**:
  - **CAN / CAN-FD**: Bosch M_CAN controllers supporting CAN 2.0 (up to 1 Mbps) and CAN-FD (64-byte payload, 2 Mbps+ data phase) with `can-utils`.
  - **RS-485**: Hardware Auto-Direction (AUD) control on `uart12` (`numaker-iot-ma35d16fj87c`).
- **Host Power Control**: GPIO-based host power state machine via `x86-power-control`.
- **Hardware Inventory & LEDs**: `entity-manager` JSON hardware profiles and `phosphor-led-manager` (`front_id`, `power`).
- **Network Discovery**: `avahi-daemon` (`${MACHINE}.local`) and OpenSSH.

---

## Storage Layout

### 1. SPI-NAND & Raw NAND (512 MB Pure UBI)

| MTD | Label | Address Range | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `mtd0` | `spinand-uboot` / `nand-uboot` | `0x00000000`–`0x00400000` | 4 MB | Raw bootloader (Header + BL2 DTB + BL2 + FIP) |
| `mtd1` | `spinand-rootfs` / `nand-rootfs` | `0x00400000`–`0x20000000` | 508 MB | UBI pool (`4064` PEBs) |

**UBI Volumes on `mtd1` (`ubi0`)**:

| Volume ID | Name | Size | Type | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `0` | `u-boot-env` | 256 KiB | dynamic | U-Boot environment (64 KiB env image) |
| `1` | `kernel-a` | 16 MiB | dynamic | Bank A kernel `Image` |
| `2` | `dtb-a` | 512 KiB | dynamic | Bank A device tree |
| `3` | `rofs-a` | 100 MiB | dynamic | Bank A read-only rootfs (`ubifs`) |
| `4` | `kernel-b` | 16 MiB | dynamic | Bank B standby kernel `Image` |
| `5` | `dtb-b` | 512 KiB | dynamic | Bank B standby device tree |
| `6` | `rofs-b` | 100 MiB | dynamic | Bank B standby read-only rootfs (`ubifs`) |
| `7` | `rwfs` | ~255 MiB | dynamic (autoresize) | Persistent overlay (`/var`) |

### 2. SD1 / eMMC (MBR Dual-Bank EXT4)

MA35 IBR reads the boot header from Sector 2 (`0x400`), which conflicts with GPT headers; SD/eMMC images therefore use an `msdos` (MBR) partition table:

| Region / Partition | Offset / Label | Size | FS | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| Raw (unpartitioned) | `0x000400`–`0x400000` | 4 MB | raw | Header (`0x400`), BL2 (`0x30000`), Env (`0x50000`), FIP (`0xC0000`) |
| Partition 1 (`p1`) | `boot-a` | 32 MB | `ext4` | Bank A `Image` + `Image.dtb` |
| Partition 2 (`p2`) | `boot-b` | 32 MB | `ext4` | Bank B `Image` + `Image.dtb` |
| Partition 3 (`p3`) | `rofs-a` | 256 MB | `ext4` | Bank A read-only rootfs |
| Partition 4 (`p4`) | — | — | Extended | MBR extended container |
| Partition 5 (`p5`) | `rofs-b` | 256 MB | `ext4` | Bank B read-only rootfs |
| Partition 6 (`p6`) | `rwfs` | 256 MB+ | `ext4` | Persistent overlay (`/var`) |

---

## Board Documentation & Test Guides

| Machine | Board Guide | Redfish API | Redfish OTA | SOL Console | CAN / CAN-FD | Power Control | RS-485 (AUD) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MA35D03F80** | [Guide](../doc/numaker-iot-ma35d03f80/README.md) | [Test](../doc/numaker-iot-ma35d03f80/test-redfish.md) | [Test](../doc/numaker-iot-ma35d03f80/test-redfish-update/README.md) | [Test](../doc/numaker-iot-ma35d03f80/test-sol.md) | [Test](../doc/numaker-iot-ma35d03f80/test-can.md) | [Test](../doc/numaker-iot-ma35d03f80/test-power-control.md) | — |
| **MA35D05KI1** | [Guide](../doc/numaker-iot-ma35d05ki1/README.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-redfish.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-redfish-update/README.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-sol.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-can.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-power-control.md) | — |
| **MA35D16FJ87C** | [Guide](../doc/numaker-iot-ma35d16fj87c/README.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-redfish.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-redfish-update/README.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-sol.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-can.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-power-control.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-rs485.md) |

---

## Layer Structure

```text
meta-evb-ma35/
├── conf/
│   ├── layer.conf
│   ├── machine/
│   │   ├── include/ma35-common.inc
│   │   ├── numaker-iot-ma35d03f80.conf
│   │   ├── numaker-iot-ma35d05ki1.conf
│   │   └── numaker-iot-ma35d16fj87c.conf
│   └── templates/default/
│       ├── bblayers.conf.sample
│       └── local.conf.sample
├── files/wic/
│   └── sdimage-ma35-dual.wks.in
├── recipes-bsp/
│   ├── tf-a/
│   │   ├── tf-a-ma35.inc
│   │   ├── tf-a-ma35_2.3.bb
│   │   └── files/ (custom DDR headers & FIP key inputs)
│   └── u-boot/
│       ├── u-boot-ma35.inc
│       ├── u-boot-ma35_2020.07.bb
│       ├── u-boot-ma35-fw-utils.bb
│       └── files/ (dual-bank boot config & DTS patches)
├── recipes-core/
│   ├── base-files/base-files_%.bbappend
│   ├── systemd/
│   │   ├── systemd_%.bbappend
│   │   └── systemd-serialgetty.bbappend
│   └── volatile-binds/volatile-binds.bbappend
├── recipes-devtools/python/
│   ├── nuwriter-pack.inc
│   ├── nuwriter-pack_1.0.bb
│   ├── python3-nuwriter-native_0.90.bb
│   └── files/ (NuWriter JSON templates & flashing scripts)
├── recipes-kernel/linux/
│   ├── linux-ma35.inc
│   ├── linux-ma35_6.6.93.bb
│   ├── files/patch-kernel-dtsi.py
│   └── linux-ma35-6.6/ (defconfigs, per-machine DTS, kernel patches)
├── recipes-nuvoton/
│   ├── ma35-soc-temp/
│   │   ├── ma35-soc-temp_1.0.bb
│   │   └── files/ (CMakeLists.txt, ma35-soc-temp.cpp, ma35-soc-temp.service)
│   └── packagegroups/packagegroup-ma35-apps.bb
├── recipes-phosphor/
│   ├── console/
│   │   ├── obmc-console_%.bbappend
│   │   └── files/ (server.ttyS4.conf, server.ttyS6.conf, server.ttyS10.conf)
│   ├── entity-manager/
│   │   ├── entity-manager_%.bbappend
│   │   └── entity-manager/ (per-machine JSON profiles)
│   ├── flash/
│   │   ├── phosphor-software-manager_%.bbappend
│   │   └── phosphor-software-manager/ (dual-bank OTA updater scripts & services)
│   ├── images/obmc-phosphor-image.bbappend
│   ├── interfaces/
│   │   ├── bmcweb_%.bbappend
│   │   └── bmcweb/ (multipart direct-to-disk streaming patch)
│   ├── leds/
│   │   ├── phosphor-led-manager_%.bbappend
│   │   └── phosphor-led-manager/led-group-config.json
│   ├── packagegroups/packagegroup-obmc-apps.bbappend
│   └── webui/
│       ├── webui-vue_%.bbappend
│       └── files/0002-add-realtime-dynamic-sensor-chart.patch
└── recipes-x86/chassis/
    ├── x86-power-control_%.bbappend
    └── x86-power-control/power-config-host0.json
```
