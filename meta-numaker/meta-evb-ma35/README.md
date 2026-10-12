# meta-evb-ma35: OpenBMC BSP Layer for Nuvoton MA35 Family

OpenBMC Board Support Package (BSP) layer for the Nuvoton MA35 Family evaluation boards.

## Table of Contents

- [Supported Machines](#supported-machines)
- [Hardware Specifications](#hardware-specifications)
- [Layer Features](#layer-features)
- [Quick Build](#quick-build)
- [SPI NAND Flash Layout](#spi-nand-flash-layout)
- [Board Documentation & Feature Guides](#board-documentation--feature-guides)
- [Layer Structure](#layer-structure)

---

## Supported Machines

| Machine | Board | SoC | Board Documentation |
| :--- | :--- | :--- | :--- |
| `numaker-iot-ma35d03f80` | NuMaker-IoT-MA35D03F80 | MA35D03F864C (dual Cortex-A35 @ 650 MHz) | [User & Operation Guide](../doc/numaker-iot-ma35d03f80/README.md) |
| `numaker-iot-ma35d05ki1` | NuMaker-IoT-MA35D05KI1 | MA35D05K (dual Cortex-A35 @ 650 MHz) | [User & Operation Guide](../doc/numaker-iot-ma35d05ki1/README.md) |
| `numaker-iot-ma35d16fj87c` | NuMaker-IoT-MA35D16FJ87C | MA35D16FJ87C (dual Cortex-A35 @ 800 MHz) | [User & Operation Guide](../doc/numaker-iot-ma35d16fj87c/README.md) |

---

## Hardware Specifications

| Item | Detail |
| :--- | :--- |
| **RAM** | 256 MB / 512 MB DDR3L (stacked in MCP) |
| **Flash** | 512 MB SPI NAND (Winbond W25N04KV / W25N01GV) |
| **Kernel** | Linux 6.6.93 (arm64) |
| **RootFS** | UBI/UBIFS on SPI NAND |
| **Debug Console** | ttyS0, 115200 8N1 |
| **Boot Flow** | SPI NAND → TF-A BL2 → BL31 → U-Boot → Linux → OpenBMC |

---

## Layer Features

- **Redfish & REST API**: `bmcweb` providing standard DMTF Redfish API (`/redfish/v1/`), telemetry, chassis/system control, sensor readings, and WebUI hosting.
- **User & Access Management**: `phosphor-user-manager` providing local user accounts, role-based access control (RBAC: `Administrator`, `Operator`, `ReadOnly`), account lockout, and password security policies via Redfish `AccountService` and WebUI.
- **WebUI Vue & Live Dynamic Sensor Chart**: `webui-vue` with custom real-time dynamic spline chart, KPI statistics (Min / Max / Avg / Trend), and live polling.
- **SoC Temperature Monitoring Daemon (`ma35-soc-temp`)**: Custom daemon reading on-die TSEN thermal sensor zone via Linux sysfs, exposing D-Bus sensor object (`/xyz/openbmc_project/sensors/temperature/cpu_thermal`) with Warning (`95°C`) and Critical (`105°C`) threshold interfaces.
- **Serial-Over-LAN (SOL) Host Console (`obmc-console`)**: Host UART routing integrated with WebUI browser-based SOL terminal (WebSocket) and SSH `obmc-console-client`.
- **Industrial Interfaces**:
  - **CAN / CAN-FD Bus**: Hardware Bosch M_CAN controllers supporting classic CAN 2.0 (up to 1 Mbps) and CAN-FD (up to 64-byte payload, 2 Mbps+ data phase), with `can-utils` suite included.
  - **Hardware RS-485**: Hardware Auto-Direction (AUD) control on UART12 (`numaker-iot-ma35d16fj87c`).
- **Host Power Control**: `x86-power-control` daemon providing GPIO-based host power on, power off, power cycle, and reset state machine management.
- **Entity Manager & Sensor Config**: Dynamic hardware inventory and configuration via `entity-manager` JSON schemas.
- **LED Management**: `phosphor-led-manager` + `phosphor-led-sysfs` with group and location indicator controls.
- **Zero-Config Networking**: `avahi-daemon` (mDNS as `${MACHINE}.local`) and OpenSSH server.

---

## Quick Build

```bash
# Setup build environment for your target machine
MACHINE=<machine-name> source setup <machine-name> build-ma35

# Build NuWriter pack image (SPI NAND, Raw NAND, SD)
bitbake nuwriter-pack
```

> [!TIP]
> For complete step-by-step build instructions (including the recommended pre-configured Docker build environment), DIP switch settings, NuWriter flashing, and boot verification, please refer to the dedicated board guide:
> - [NuMaker-IoT-MA35D03F80 Guide](../doc/numaker-iot-ma35d03f80/README.md)
> - [NuMaker-IoT-MA35D05KI1 Guide](../doc/numaker-iot-ma35d05ki1/README.md)
> - [NuMaker-IoT-MA35D16FJ87C Guide](../doc/numaker-iot-ma35d16fj87c/README.md)
> - [Docker Build Environment Guide](../doc/docker/README.md)

---

## SPI NAND Flash Layout

Total: 512 MB (`0x0`–`0x10000000`)

| MTD | Label | Address Range | Size | Contents |
| :--- | :--- | :--- | :--- | :--- |
| `mtd0` | `spinand-uboot` | `0x000000`–`0x300000` | 3 MB | Header + BL2 + FIP (BL31+U-Boot) |
| `mtd1` | `spinand-uboot-env` | `0x300000`–`0x3C0000` | 768 KB | U-Boot environment |
| `mtd2` | `spinand-device-tree` | `0x3C0000`–`0x400000` | 256 KB | Linux DTB |
| `mtd3` | `spinand-kernel` | `0x400000`–`0x1C00000` | 24 MB | Linux kernel (Image) |
| `mtd4` | `spinand-rootfs` | `0x1C00000`–`0x10000000` | 228 MB | UBI volume (UBIFS rootfs) |

---

## Board Documentation & Feature Guides

Each supported machine provides dedicated operational and feature test documentation:

| Board / Machine | Main Guide | Redfish Test Suite | SOL Host Console | CAN / CAN-FD Bus | Host Power Control | RS-485 (AUD) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MA35D03F80** | [Guide](../doc/numaker-iot-ma35d03f80/README.md) | [Test](../doc/numaker-iot-ma35d03f80/test-redfish.md) | [Test](../doc/numaker-iot-ma35d03f80/test-sol.md) | [Test](../doc/numaker-iot-ma35d03f80/test-can.md) | [Test](../doc/numaker-iot-ma35d03f80/test-power-control.md) | — |
| **MA35D05KI1** | [Guide](../doc/numaker-iot-ma35d05ki1/README.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-redfish.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-sol.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-can.md) | [Test](../doc/numaker-iot-ma35d05ki1/test-power-control.md) | — |
| **MA35D16FJ87C** | [Guide](../doc/numaker-iot-ma35d16fj87c/README.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-redfish.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-sol.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-can.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-power-control.md) | [Test](../doc/numaker-iot-ma35d16fj87c/test-rs485.md) |

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
├── recipes-bsp/
│   ├── tf-a/
│   │   ├── tf-a-ma35.inc
│   │   ├── tf-a-ma35_2.3.bb
│   │   └── files/ (DDR headers: MA35D03F80.h, MA35D05KI1.h, MA35D16FJ87C.h)
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
│   └── linux-ma35-6.6/ (defconfigs, per-machine DTS)
├── recipes-nuvoton/
│   ├── ma35-soc-temp/
│   │   ├── CMakeLists.txt
│   │   ├── ma35-soc-temp.cpp
│   │   ├── ma35-soc-temp.service
│   │   └── ma35-soc-temp_1.0.bb
│   └── packagegroups/
│       └── packagegroup-ma35-apps.bb
├── recipes-phosphor/
│   ├── console/
│   │   ├── files/server.ttyS4.conf
│   │   ├── files/server.ttyS6.conf
│   │   ├── files/server.ttyS10.conf
│   │   └── obmc-console_%.bbappend
│   ├── entity-manager/
│   │   ├── entity-manager_%.bbappend
│   │   └── entity-manager/ (per-machine JSON configs)
│   ├── images/obmc-phosphor-image.bbappend
│   ├── interfaces/bmcweb_%.bbappend
│   ├── leds/
│   │   ├── phosphor-led-manager/led-group-config.json
│   │   └── phosphor-led-manager_%.bbappend
│   ├── packagegroups/packagegroup-obmc-apps.bbappend
│   └── webui/
│       ├── files/0002-add-realtime-dynamic-sensor-chart.patch
│       └── webui-vue_%.bbappend
└── recipes-x86/chassis/
    ├── x86-power-control_%.bbappend
    └── x86-power-control/power-config-host0.json
```
