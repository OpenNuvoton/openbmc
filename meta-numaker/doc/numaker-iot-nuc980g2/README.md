# NuMaker-IoT-NUC980G2 OpenBMC Quickstart & Reference

Operational guide for building, flashing, and verifying OpenBMC on the **Nuvoton NuMaker-IoT-NUC980G2** evaluation board. The board acts as an out-of-band BMC controlling an external host via Redfish, SSH CLI, and GPIO power signals (`POWER_OUT`, `RESET_OUT`, `PS_PWROK`).

---

## 1. Hardware Specifications & Setup

### 1.1 Specifications

| Item | Detail |
| :--- | :--- |
| **Board** | NuMaker-IoT-NUC980G2 |
| **SoC** | Nuvoton NUC980DK71YC (ARM926EJ-S @ 300 MHz) |
| **RAM** | 128 MB DDR2 (stacked in MCP) |
| **Flash** | 128 MB SPI NAND (Winbond W25N01GV) |
| **Kernel** | Linux 6.6.93 (armv5te) |
| **Debug Console** | UART0 (`/dev/ttyS0`), 115200 8N1 |
| **Network** | 10/100M Ethernet (RMII) |
| **Default IP / mDNS** | DHCP or `numaker-iot-nuc980g2.local` |
| **Default Credentials** | `root` / `0penBmc` |

### 1.2 Connectors

- **Debug Serial Console (UART0)**: Micro-USB to board **VCOM** port (or header `PE14`/`PE15`), 115200 8N1.
- **NuWriter Programming Port (USB Device)**: Micro-USB to board **USB (Device)** port. *(Do not connect NuWriter to VCOM or Host USB ports).*
- **Ethernet (LAN)**: RJ45 cable to local network (DHCP).
- **Power**: 5V Micro-USB to dedicated power port.
- **Boot Mode DIP Switch**:
  - **USB Boot (Download Mode)**: Set DIP switch for USB download when flashing with NuWriter.
  - **SPI NAND Boot (Normal Run Mode)**: Set DIP switch for SPI NAND boot to run OpenBMC.

---

## 2. Build Environment & Compilation

Build OpenBMC inside the tested Ubuntu 24.04 Docker environment (details in [`../docker/README.md`](../docker/README.md)).
Ensure at least **60 GB** of free disk space for toolchain builds and sstate cache.

### 2.1 Build Steps (Docker)

```bash
# 1. Build and enter the container (run once)
cd meta-numaker/doc/docker/
./build.sh
./join.sh

# 2. Inside the container, clone and initialize the build directory:
cd ~/shared
git clone -b numaker https://github.com/OpenNuvoton/openbmc.git
cd openbmc
MACHINE=numaker-iot-nuc980g2 source setup numaker-iot-nuc980g2 build-nuc980

# 3. Start compilation:
bitbake nuwriter-pack
```

> [!NOTE]
> For subsequent sessions in a new shell:
> ```bash
> cd ~/shared/openbmc
> source oe-init-build-env build-nuc980
> bitbake nuwriter-pack
> ```

### 2.2 Build Outputs

Deploy directory: `build-nuc980/tmp/deploy/images/numaker-iot-nuc980g2/`

```text
├── nuwriter-pack-numaker-iot-nuc980g2.bin   (SPI NAND pack image)
├── install_nuwriter.bat                     (NuWriter environment installer)
└── nuwriter_program.bat                     (One-click flasher script)
```

### 2.3 Prebuilt Artifacts from GitHub Actions

Precompiled zip packages are available from the CI pipeline:
1. Go to: [OpenBMC GitHub Actions Workflow](https://github.com/OpenNuvoton/openbmc/actions/workflows/numaker.yml).
2. Select the latest successful build.
3. Download `openbmc-numaker-iot-nuc980g2.zip` from **Artifacts** and extract it on Windows.

---

## 3. Firmware Flashing (NuWriter)

Requires [NuWriter for NUC980 (Windows)](https://github.com/OpenNuvoton/NUC980_NuWriter).

> [!TIP]
> If NuWriter reports `No device connected`:
> - Confirm the DIP switch is set to **USB Boot (Download Mode)**.
> - Verify the cable is connected to **USB (Device)**, not VCOM.
> - Check Windows Device Manager for the Nuvoton USB driver.

### 3.1 Flashing Steps

1. Set the board DIP switch to **USB Boot** mode.
2. Connect the board's USB Device port to the Windows PC and power on.
3. In NuWriter:
   - Verify device is recognized as `NUC980`.
   - Select **Target**: `SPI NAND`.
   - In **Erase** tab $\rightarrow$ select **Erase All** $\rightarrow$ click **Erase**.
   - In **Burn** tab $\rightarrow$ set **Type**: `Pack` $\rightarrow$ select `nuwriter-pack.bin` $\rightarrow$ click **Burn**.
4. Power off $\rightarrow$ switch DIP switch to **SPI NAND Boot** mode $\rightarrow$ power on.

---

## 4. Boot Verification & Sanity Checks

### 4.1 Expected Serial Boot Log (UART0, 115200 8N1)

```text
U-Boot SPL 2020.07 (Oct 12 2026 - 15:00:00 +0800)
Trying to boot from SPI NAND

U-Boot 2020.07 (Oct 12 2026 - 15:00:00 +0800)
CPU: NUC980
DRAM:  128 MiB
NAND:  128 MiB
Loading Kernel from 0x00200000 ...
Booting Kernel ...
Starting kernel ...

[    0.000000] Booting Linux on physical CPU 0x0
[    0.000000] Linux version 6.6.93 (oe-user@oe-host) ...
...
[  OK  ] Started Phosphor Web Server (bmcweb).
[  OK  ] Started Dropbear SSH daemon.

OpenBMC Release 2.14.0-dev
numaker-iot-nuc980g2 login:
```

### 4.2 Network & Access

- **mDNS Hostname Resolution**:
  ```bash
  ping -c 3 numaker-iot-nuc980g2.local
  ```
  *(If mDNS is blocked on your router, log into UART0 and check `ip addr show eth0`).*

- **SSH Access**:
  ```bash
  ssh root@numaker-iot-nuc980g2.local
  # Password: 0penBmc
  ```

- **Redfish REST API**:
  > [!NOTE]
  > Due to memory constraints (128 MB RAM), `webui-vue` is omitted on NUC980. Management is performed directly via Redfish API (`https://<BMC-IP>/redfish/v1/`) and SSH.

  Query service root:
  ```bash
  curl -k -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/ | jq .
  ```

---

## 5. Subsystem Verification

### 5.1 Redfish Regression Test Suite

Requires `curl` and `jq` on the test host:

```bash
cd doc/numaker-iot-nuc980g2/
chmod +x test-redfish.sh
./test-redfish.sh
```

**Output:**
```text
====================================================
     NUC980 OpenBMC Functions Integration Test    
====================================================
[Test] GET Service Root...
✓ Passed (HTTP 200)
[Test] GET Chassis Details (system)...
✓ Passed (HTTP 200)
[Test] GET System details...
✓ Passed (HTTP 200)
[Test] Power Control Tests...
POST Host Power On: ✓ Passed (HTTP 204)
GET Verify Host PowerState: ✓ Passed (PowerState=On)
====================================================
Test Summary: All Tests Passed!
Report generated: test-redfish.md
====================================================
```

See [`test-redfish.md`](test-redfish.md) for full compliance results.

### 5.2 Manual Redfish API Checks

```bash
# Service Root
curl -k -s -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/ | jq .

# Chassis Status
curl -k -s -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/Chassis/system | jq '{Id, Name, Status, PowerState}'

# Location Indicator LED (Turn ON)
curl -k -s -u root:0penBmc -X PATCH \
  https://numaker-iot-nuc980g2.local/redfish/v1/Chassis/system \
  -H "Content-Type: application/json" \
  -d '{"LocationIndicatorActive": true}' -i
# Expected: HTTP/1.1 204 No Content
```

### 5.3 Host Power Control (GPIO)

| Signal | Direction | Pin | Description |
| :--- | :--- | :--- | :--- |
| **`POWER_OUT`** | Output | **`PD12`** | Power Button (Active Low, 200ms on, 4s force off) |
| **`RESET_OUT`** | Output | **`PD13`** | Reset Button (Active Low, 200ms) |
| **`PS_PWROK`** | Input | **`PF9`** | Host PSU Power Good status (Active High 3.3V) |

> [!NOTE]
> `x86-power-control` verifies host power status on `PF9`. When testing standalone:
> - **Power On**: Connect `PF9` to **3.3V** before or immediately after issuing the Power On command.
> - **Power Off / Force Off**: Disconnect `PF9` (or pull to **GND**) after issuing the Power Off command.

```bash
# Power On:
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}' -i
# Expected: HTTP/1.1 204 No Content

# Verify PowerState:
curl -k -s -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system | jq .PowerState
# Expected: "On"

# Force Off:
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceOff"}' -i
# Expected: HTTP/1.1 204 No Content
```

See [`test-power-control.md`](test-power-control.md) for signal timings and wiring diagrams.

---

## 6. Document Index

- [`test-redfish.md`](test-redfish.md): Full Redfish integration test results and schema compliance matrix.
- [`test-redfish.sh`](test-redfish.sh): Automated curl test script for Redfish regression testing.
- [`test-power-control.md`](test-power-control.md): Wiring diagram, signal timings, and manual GPIO verification guide.
