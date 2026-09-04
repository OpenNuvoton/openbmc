# meta-evb-ma35: OpenBMC BSP Layer for Nuvoton MA35 Family

OpenBMC Board Support Package for the Nuvoton MA35 Family evaluation boards.

## Table of Contents

- [Supported Machines](#supported-machines)
- [Hardware Specifications](#hardware-specifications)
- [Features](#features)
- [Build](#build)
- [Flashing (NuWriter)](#flashing-nuwriter)
- [SPI NAND Flash Layout](#spi-nand-flash-layout)
- [Feature Guides & Testing](#feature-guides--testing)
  - [Redfish API & Testing](#redfish-api)
  - [User Management & RBAC](#user-management--rbac)
  - [SoC Temperature Monitoring & WebUI Live Chart](#soc-temperature-monitoring--webui-live-chart)
  - [Serial-Over-LAN (SOL) Console](#serial-over-lan-sol-console)
  - [CAN / CAN-FD Bus](#can--can-fd-bus)
  - [Host Power Control](#host-power-control)
- [Layer Structure](#layer-structure)

---

## Supported Machines

| Machine | Board | SoC |
|---------|-------|-----|
| `numaker-iot-ma35d03f80` | NuMaker-IoT-MA35D03F80 | MA35D03F864C (dual Cortex-A35 @ 650 MHz) |
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

- **Redfish & REST API**: `bmcweb` providing standard DMTF Redfish API (`/redfish/v1/`), telemetry, chassis/system control, sensor readings, and WebUI hosting.
- **User & Access Management**: `phosphor-user-manager` providing local user accounts, role-based access control (RBAC: `Administrator`, `Operator`, `ReadOnly`), account lockout, and password security policies via Redfish `AccountService` and WebUI.
- **WebUI Vue & Live Dynamic Sensor Chart**: `webui-vue` with custom real-time dynamic spline chart, KPI statistics (Min / Max / Avg / Trend), and live polling.
- **SoC Temperature Monitoring Daemon (`ma35-soc-temp`)**: Custom daemon reading on-die TSEN thermal sensor zone via Linux sysfs, exposing D-Bus sensor object (`/xyz/openbmc_project/sensors/temperature/cpu_thermal`) with Warning (`95°C`) and Critical (`105°C`) threshold interfaces.
- **Serial-Over-LAN (SOL) Host Console (`obmc-console`)**: Host UART routing (UART6 `/dev/ttyS6`, PN14/PN15 on `numaker-iot-ma35d03f80`, **requires J63 Pin 1-2 shorted for RS-232 mode**; UART4 `/dev/ttyS4`, PI10/PI11 on `numaker-iot-ma35d05ki1`), integrated with WebUI browser-based SOL terminal (WebSocket) and SSH `obmc-console-client`.
- **Additional Serial Interfaces**: Hardware UART16 enabled on `numaker-iot-ma35d03f80` (`/dev/ttyS16`, PD8/PD9/PD10/PD11 for CTS/RTS/RXD/TXD 5-wire support).
- **CAN / CAN-FD Industrial Bus Support**: Hardware Bosch M_CAN controllers (CAN0 on PN2/PN3, CAN1 on PN6/PN7, CAN3 on PM2/PM3), supporting classic CAN 2.0 (up to 1 Mbps) and CAN-FD (up to 64-byte payload, 2 Mbps+ data phase), with `can-utils` suite included.
- **Host Power Control**: `x86-power-control` daemon providing GPIO-based host power on, power off, power cycle, and reset state machine management.
- **Entity Manager**: Dynamic hardware inventory and configuration via `entity-manager` JSON schemas.
- **LED Management**: `phosphor-led-manager` + `phosphor-led-sysfs` with group and location indicator controls.
- **Zero-Config Networking & Remote Access**: `avahi-daemon` (mDNS as `${MACHINE}.local`) and OpenSSH server.

---

## Build

```bash
# numaker-iot-ma35d05ki1
MACHINE=numaker-iot-ma35d05ki1 source setup numaker-iot-ma35d05ki1 build-ma35
bitbake nuwriter-pack

# numaker-iot-ma35d03f80
MACHINE=numaker-iot-ma35d03f80 source setup numaker-iot-ma35d03f80 build-ma35
bitbake nuwriter-pack
```

Output: `tmp/deploy/images/${MACHINE}/nuwriter-pack-${MACHINE}.bin`

> On subsequent builds, just `source oe-init-build-env build-ma35` to re-enter.

### Prebuilt Images

Prebuilt images are available from GitHub Actions:

[OpenBMC building → Artifacts](https://github.com/OpenNuvoton/openbmc/actions/workflows/numaker.yml)

1. Open the workflow page and select the latest successful run.
2. Scroll to the **Artifacts** section at the bottom.
3. Download the artifact for your machine (`numaker-iot-ma35d03f80` or `numaker-iot-ma35d05ki1`).
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
numaker-iot login:
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

## Feature Guides & Testing

BMC is accessible via mDNS hostname: `${MACHINE}.local` (e.g. `numaker-iot-ma35d03f80.local`, `numaker-iot-ma35d05ki1.local`).

### Redfish API

- **Automated Test Guides**:
  - `numaker-iot-ma35d03f80`: [doc/test-redfish/numaker-iot-ma35d03f80.md](../../doc/test-redfish/numaker-iot-ma35d03f80.md) (Script: `doc/test-redfish/numaker-iot-ma35d03f80.sh`)
  - `numaker-iot-ma35d05ki1`: [doc/test-redfish/numaker-iot-ma35d05ki1.md](../../doc/test-redfish/numaker-iot-ma35d05ki1.md) (Script: `doc/test-redfish/numaker-iot-ma35d05ki1.sh`)

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

### User Management & RBAC

OpenBMC provides role-based user management via `phosphor-user-manager` and Redfish `AccountService`:

- **WebUI User Management**: Access `https://${MACHINE}.local/#/access-control/local-users` to add/edit/remove accounts, change passwords, and configure roles.
- **Redfish Account API**:
  ```bash
  # List all local accounts
  curl -k -s -u root:0penBmc https://${MACHINE}.local/redfish/v1/AccountService/Accounts

  # Create a new Operator user
  curl -k -s -u root:0penBmc -X POST \
    https://${MACHINE}.local/redfish/v1/AccountService/Accounts \
    -H "Content-Type: application/json" \
    -d '{"UserName": "operator1", "Password": "Password123!", "RoleId": "Operator", "Enabled": true}'

  # Change user password
  curl -k -s -u root:0penBmc -X PATCH \
    https://${MACHINE}.local/redfish/v1/AccountService/Accounts/operator1 \
    -H "Content-Type: application/json" \
    -d '{"Password": "NewPassword456!"}'
  ```

### SoC Temperature Monitoring & WebUI Live Chart

- **Daemon**: `ma35-soc-temp` polls `/sys/class/thermal/thermal_zone0/temp`.
- **D-Bus Object**: `/xyz/openbmc_project/sensors/temperature/cpu_thermal`
- **Redfish Endpoint**: `https://${MACHINE}.local/redfish/v1/Chassis/system/Thermal`
- **WebUI Dynamic Chart**: Access WebUI at `https://${MACHINE}.local/#/hardware-status/sensors` to view the real-time live sensor spline chart with Min/Max/Avg/Trend KPIs.

### Serial-Over-LAN (SOL) Console

- **Detailed Guides & Wiring**:
  - `numaker-iot-ma35d03f80`: [doc/test-sol/numaker-iot-ma35d03f80.md](../../doc/test-sol/numaker-iot-ma35d03f80.md)
  - `numaker-iot-ma35d05ki1`: [doc/test-sol/numaker-iot-ma35d05ki1.md](../../doc/test-sol/numaker-iot-ma35d05ki1.md)
- **Hardware Pins**: `PI10` (`UART4_RXD`) / `PI11` (`UART4_TXD`)
- **WebUI SOL Access**: `https://${MACHINE}.local/#/operations/serial-over-lan`
- **SSH SOL Access**: `ssh -t root@${MACHINE}.local obmc-console-client`

### CAN / CAN-FD Bus

- **Detailed Guides & Testing**:
  - `numaker-iot-ma35d03f80`: [doc/test-can/numaker-iot-ma35d03f80.md](../../doc/test-can/numaker-iot-ma35d03f80.md)
  - `numaker-iot-ma35d05ki1`: [doc/test-can/numaker-iot-ma35d05ki1.md](../../doc/test-can/numaker-iot-ma35d05ki1.md)
- **Hardware Pins**: `PG8` (`CAN3_RXD`) / `PG9` (`CAN3_TXD`)
- **Quick Bring-up (CAN-FD 500k/2M)**:
  ```bash
  ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
  candump can0 &
  cansend can0 123##30102030405060708090A0B0C0D0E0F
  ```

### Host Power Control

- **Wiring & Pin Assignment**:
  - `numaker-iot-ma35d03f80`: [doc/x86-power-control/numaker-iot-ma35d03f80.md](../../doc/x86-power-control/numaker-iot-ma35d03f80.md) (`PN1` POWER_OUT / `PN0` RESET_OUT / `PK12` PS_PWROK)
  - `numaker-iot-ma35d05ki1`: [doc/x86-power-control/numaker-iot-ma35d05ki1.md](../../doc/x86-power-control/numaker-iot-ma35d05ki1.md) (`PC2` POWER_OUT / `PC3` RESET_OUT / `PC7` PS_PWROK)

---

## Layer Structure

```
meta-evb-ma35/
├── conf/
│   ├── layer.conf
│   ├── machine/
│   │   ├── include/ma35-common.inc
│   │   ├── numaker-iot-ma35d03f80.conf
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
