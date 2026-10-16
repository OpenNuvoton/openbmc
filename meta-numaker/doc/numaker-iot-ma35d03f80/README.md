# NuMaker-IoT-MA35D03F80 OpenBMC User & Operation Guide

This document provides a comprehensive, end-to-end operational guide for developers and engineers to build, flash, verify, and validate all OpenBMC features on the **Nuvoton NuMaker-IoT-MA35D03F80** evaluation board.

> [!NOTE]
> **What is OpenBMC & System Role**:
> OpenBMC is an open-source Linux distribution for Baseboard Management Controllers (BMCs). In server and edge systems, this evaluation board acts as a **BMC (Management Controller)** to remotely monitor, manage, and recover an external target computer (**Host**). Management tasks are performed out-of-band over the network using DMTF Redfish REST APIs, WebUI, Serial-Over-LAN (SOL) host console routing, and GPIO host power control (`POWER_OUT`, `RESET_OUT`, `PS_PWROK`).

---

## 1. Hardware Specifications & Setup

### 1.1 Specifications

| Item | Detail |
| :--- | :--- |
| **Board** | NuMaker-IoT-MA35D03F80 (NuMaker-IoT-MA35D0-A1) |
| **SoC** | Nuvoton MA35D03F864C (Dual Cortex-A35 @ 650 MHz) |
| **RAM** | 256 MB DDR3L (stacked in MCP) |
| **Storage Support** | **SPI NAND** (512MB), **Raw NAND** (NFI), **MicroSD / SD** (SDHCI1) |
| **Debug Console** | UART0 (`/dev/ttyS0`), 115200 8N1 |
| **Host SOL Console** | UART6 (`/dev/ttyS6`), Pins `PN14` (RX) / `PN15` (TX) |
| **CAN Bus** | 3× Bosch M_CAN: CAN0 (`PN2`/`PN3`), CAN1 (`PN6`/`PN7`), CAN3 (`PM2`/`PM3`) |
| **Power Control** | GPIO: `POWER_OUT` (`PN1`), `RESET_OUT` (`PN0`), `PS_PWROK` (`PK12`) |
| **Network** | 10/100M Ethernet (RMII0 / RMII1) |
| **Default IP / mDNS** | DHCP or `numaker-iot-ma35d03f80.local` |
| **Default Credentials** | Username: `root` / Password: `0penBmc` |

### 1.2 Hardware Connectors & Interface Setup

Before getting started, identify the physical connectors on the board:
- **Debug Serial Console (UART0)**: Connect a Micro-USB cable to the board's **VCOM (Virtual COM)** port. Open a serial terminal (PuTTY, Tera Term, or minicom) set to **115200 baud, 8 data bits, no parity, 1 stop bit, no flow control**.
- **NuWriter Programming Port (USB0 Device)**: Connect a Micro-USB cable to the **USB0 (Device)** port when burning firmware. *(Do not connect NuWriter to the VCOM or Host USB ports).*
- **Ethernet Port (LAN)**: Connect an RJ45 Ethernet cable to your local router or switch (DHCP required).
- **Power Port**: Power the board with a 5V power cable (USB Type-C connector).

### 1.3 Key Hardware Jumpers & Switches

#### Boot Mode DIP Switch Settings (SW7)

Configure the 8-position power-on setting DIP switch (**SW7**) on the NuMaker board for programming (**Burn to**) or booting (**Boot from**):

**DIP Switch SW7 Pin Definition (PG0~PG7 internal pull-down, 10K pull-up to VDD3V3):**
- **Switch 1 (PG0)**: Secure Boot (`ON`: Disable, `OFF`: Enable)
- **Switch 2 (PG1)**: Boot Source QSPI0, SD/eMMC I/O Voltage (`OFF`: 3.3V, `ON`: 1.8V)
- **Switch 3 (PG2)**: Boot Source Select [bit 0]
- **Switch 4 (PG3)**: Boot Source Select [bit 1]
  - `PG3=L, PG2=L`: QSPI0 Flash
  - `PG3=L, PG2=H`: SD/eMMC
  - `PG3=H, PG2=L`: NAND Flash
  - `PG3=H, PG2=H`: USB
- **Switch 5 (PG4)**: USB Boot: `OFF`=USBD (Device), `ON`=USBH (Host) / NAND Page Size [bit 0]
- **Switch 6 (PG5)**: USBH Port: `OFF`=Port 0, `ON`=Port 1 / NAND Page Size [bit 1]
- **Switch 7 (PG6)**: QSPI0: `OFF`=SPI-NAND 1-bit / SD/eMMC: `OFF`=SD0, `ON`=SD1 / NAND BCH [bit 0]
- **Switch 8 (PG7)**: QSPI0: `OFF`=SPI-NAND 1-bit, `ON`=SPI-NOR 1-bit / SD/eMMC: `OFF`=4-bit, `ON`=Not Supported / NAND BCH [bit 1]

**Power-on Setting Logic:**
- **ON (H)**: Switch set to ON (Pulled UP to 3.3V)
- **OFF (L)**: Switch set to OFF (Internal pull-down to Low)

| Memory Storage | **Burn to** settings (USB Download Mode) | **Boot from** settings (Run Mode) |
| :--- | :--- | :--- |
| **Serial NAND (SPI NAND)**<br>(QSPI0 Flash, SPI-NAND 1-bit) | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 3 (PG2) to ON</li><li>Switch 4 (PG3) to ON</li><li>Switch Others (2, 5, 6, 7, 8) to OFF</li></ul>*(Summary: Switch 1, 3, 4 ON; Others OFF)* | <ul><li>Switch 1 (PG0) to ON</li><li>Switch Others (2, 3, 4, 5, 6, 7, 8) to OFF</li></ul>*(Summary: Switch 1 ON; Others OFF)* |
| **SD Card**<br>(Select SD1 slot, 4-bit mode) | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 3 (PG2) to ON</li><li>Switch 4 (PG3) to ON</li><li>Switch 7 (PG6) to ON (SD1)</li><li>Switch Others (2, 5, 6, 8) to OFF</li></ul>*(Summary: Switch 1, 3, 4, 7 ON; Switch 2, 5, 6, 8 OFF)* | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 3 (PG2) to ON</li><li>Switch 7 (PG6) to ON (SD1)</li><li>Switch 8 (PG7) to OFF (4-bit)</li><li>Switch Others (2, 4, 5, 6, 8) to OFF</li></ul>*(Summary: Switch 1, 3, 7 ON; Switch 2, 4, 5, 6, 8 OFF)* |
| **Raw NAND**<br>(Select Ignore BCH and Page setting) | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 3 (PG2) to ON</li><li>Switch 4 (PG3) to ON</li><li>Switch Others (2, 5, 6, 7, 8) to OFF</li></ul>*(Summary: Switch 1, 3, 4 ON; Others OFF)* | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 4 (PG3) to ON</li><li>Switch Others (2, 3, 5, 6, 7, 8) to OFF</li></ul>*(Summary: Switch 1, 4 ON; Others OFF)* |

#### Jumper J63 (UART6 RS-232 / RS-485 Selection) — CRITICAL ⚠️
- **J63 PIN 1-2 MUST BE SHORTED** for Serial-Over-LAN (SOL) RS-232 mode.
- If open or set to RS-485, the RS-232 receiver is disconnected and host keystrokes cannot be received.

---

## 2. OpenBMC Build Environment & Compilation

To ensure reproducible builds and avoid package version conflicts on host distributions, building OpenBMC is performed using the pre-configured Docker container environment (Ubuntu 24.04 with all necessary Yocto dependencies).

> [!IMPORTANT]
> **First-Time Build Resources & Expectations**:
> - **Disk Space**: Yocto/Bitbake downloads upstream source archives and builds cross-compilation toolchains from source. Ensure your host has at least **50~100 GB** of free disk space.
> - **Build Duration**: The initial build typically takes **1 to 3 hours** depending on CPU core count and network bandwidth. Subsequent builds utilize `sstate-cache` and complete in minutes.
> - **Network Fetch Retries**: If any transient network fetch error occurs while downloading upstream packages, simply re-run `bitbake nuwriter-pack` to resume downloading from where it stopped.

---

### 2.1 Building OpenBMC via Docker (Recommended)

> [!TIP]
> **Complete Docker Documentation**: Please refer to [`../docker/README.md`](../docker/README.md) for full Docker installation, container creation, and management instructions.

**Quick Start via Docker:**

```bash
# 1. Enter the docker directory and build the container (run once)
cd meta-numaker/doc/docker/
./build.sh

# 2. Attach to the build container
./join.sh

# 3. Inside the container, enter the shared directory and start the build:
cd ~/shared
git clone -b numaker https://github.com/OpenNuvoton/openbmc.git
cd openbmc
MACHINE=numaker-iot-ma35d03f80 source setup numaker-iot-ma35d03f80 build-ma35
bitbake nuwriter-pack
```

> **Note**: For subsequent builds in a new terminal session, execute:
> ```bash
> cd ~/shared/openbmc
> source oe-init-build-env build-ma35
> bitbake nuwriter-pack
> ```

---

### 2.2 Build Output Directory

**Build Output Directory:** `build-ma35/tmp/deploy/images/numaker-iot-ma35d03f80/`

```text
├── nuwriter-pack-spinand-numaker-iot-ma35d03f80.bin   (SPI NAND image)
├── nuwriter-pack-nand-numaker-iot-ma35d03f80.bin      (Raw NAND image)
├── nuwriter-pack-sd-numaker-iot-ma35d03f80.bin        (SD card image)
├── install_nuwriter.bat                               (NuWriter environment installer)
├── nuwriter_program_spinand.bat                       (SPI NAND one-click flasher)
├── nuwriter_program_nand.bat                          (Raw NAND one-click flasher)
└── nuwriter_program_sd.bat                            (SD card one-click flasher)
```

---

### 2.3 Downloading Prebuilt Artifacts from GitHub Actions

You can download pre-built artifacts directly from GitHub Actions without compiling locally:
1. Navigate to: [OpenBMC building GitHub Actions Workflow](https://github.com/OpenNuvoton/openbmc/actions/workflows/numaker.yml)
2. Select the latest successful build.
3. In the **Artifacts** section, download `openbmc-numaker-iot-ma35d03f80.zip`.
4. Extract the zip file to your Windows PC.

---

## 3. Firmware Flashing Procedure (NuWriter)

Flashing on Windows uses Nuvoton's Python-based **NuWriter** tool via command-line batch scripts.

> [!TIP]
> **Flashing Troubleshooting**:
> - **Device Not Detected**: Ensure the board DIP switch (SW7) is set to **USB Download Mode** (Switch 1, 3, 4 to ON; Switch 2, 5, 6, 7, 8 to OFF) and your USB cable is plugged into the **USB0 (Device)** port (not VCOM).
> - **Windows USB Driver**: If NuWriter reports `No USB device found`, open Windows Device Manager and check whether a Nuvoton USB device or WinUSB device is recognized.

### 3.1 Setup (First Time Only)

1. Connect the board's **USB0 (Device)** port to your Windows PC with a USB cable.
2. In the extracted folder, double-click:
   ```cmd
   install_nuwriter.bat
   ```
   This automatically downloads and extracts `MA35D1_NuWriter` with the required DDR initializers.

### 3.2 Flashing to SPI NAND Flash

1. Set the board DIP switch (SW7) to **USB Download Mode** (Switch 1, 3, 4 to ON; Others to OFF) and power on the board.
2. Run the SPI NAND flashing script:
   ```cmd
   nuwriter_program_spinand.bat
   ```
3. **Expected Execution Output:**
   ```text
   ============================================
    numaker-iot-ma35d03f80 SPI-NAND Programming Script
   ============================================

   Make sure the board is in USB download mode.

   [1/3] Initializing DDR...
   Successfully get info from 1 device(s)
   [2/3] Erasing SPI-NAND flash...
   100%|##########
   Successfully erased 1 device(s)
   [3/3] Programming SPI-NAND flash...
   device 0 Programming: 100%|##########
   Programming completed successfully!
   Reset the board to boot from SPI-NAND.
   ```
4. Power off $\rightarrow$ Set DIP switch (SW7) to **SPI NAND Boot** (Switch 1 to ON; Others to OFF) $\rightarrow$ Power on.

### 3.3 Flashing to Raw NAND Flash

1. Set the board DIP switch (SW7) to **USB Download Mode** (Switch 1, 3, 4 to ON; Others to OFF) and power on.
2. Run the Raw NAND flashing script:
   ```cmd
   nuwriter_program_nand.bat
   ```
3. **Expected Output:**
   ```text
   [1/3] Initializing DDR...
   [2/3] Erasing entire NAND flash...
   100%|##########
   [3/3] Programming NAND flash...
   device 0 Programming: 100%|##########
   Programming completed successfully!
   ```
4. Power off $\rightarrow$ Set DIP switch (SW7) to **Raw NAND Boot** (Switch 1, 4 to ON; Others to OFF) $\rightarrow$ Power on.

### 3.4 Flashing to MicroSD Card

1. Insert MicroSD card into the board slot. Set board DIP switch (SW7) to **USB Download Mode for SD1** (Switch 1, 3, 4, 7 to ON; Switch 2, 5, 6, 8 to OFF) and power on.
2. Run:
   ```cmd
   nuwriter_program_sd.bat
   ```
3. Power off $\rightarrow$ Set DIP switch (SW7) to **SD Boot** (Switch 1, 3, 7 to ON; Others to OFF) $\rightarrow$ Power on.

---

## 4. Boot Verification & Sanity Checks

### 4.1 Expected Serial Boot Log (UART0, 115200 8N1)

```text
NOTICE:  BL2: v2.8(release):
NOTICE:  BL2: Built : 15:30:00, Oct 12 2026
NOTICE:  BL2: Normal boot
NOTICE:  BL31: v2.8(release):
NOTICE:  BL31: Built : 15:30:00, Oct 12 2026

U-Boot 2020.07 (Oct 12 2026 - 15:30:00 +0800)
CPU: MA35D03F864C (Cortex-A35 dual core @ 650 MHz)
DRAM:  256 MiB
NAND:  512 MiB
Loading Kernel from storage...
Booting Kernel ...
Starting kernel ...

[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x410fd041]
[    0.000000] Linux version 6.6.93-ma35 (oe-user@oe-host) ...
...
[  OK  ] Started Phosphor Web Server (bmcweb).
[  OK  ] Started MA35 SoC Temperature Monitor (ma35-soc-temp).
[  OK  ] Started Serial-Over-LAN Console Server (obmc-console-server).
[  OK  ] Started Dropbear SSH daemon.

OpenBMC Release 2.14.0-dev
numaker-iot-ma35d03f80 login:
```

### 4.2 Network & WebUI Access

- **mDNS Hostname Resolution**:
  ```bash
  ping -c 3 numaker-iot-ma35d03f80.local
  ```
  > [!TIP]
  > **IP Address Fallback**: If `.local` does not resolve in your network (e.g. mDNS/multicast is blocked by your router), log into the serial console (UART0) and run `ip addr show eth0` to view the assigned IPv4 address.

- **SSH Access**:
  ```bash
  ssh root@numaker-iot-ma35d03f80.local
  # Password: 0penBmc
  ```

- **WebUI Browser Access**:
  Open `https://numaker-iot-ma35d03f80.local/` (or `https://<BMC-IP>/`) in your browser.
  > [!NOTE]
  > **Browser HTTPS Security Warning**: OpenBMC uses a self-signed SSL certificate by default. When the browser displays `Your connection is not private` (or `NET::ERR_CERT_AUTHORITY_INVALID`), click **Advanced** and select **Proceed to <ip> (unsafe)** to open the OpenBMC WebUI. Log in with `root` / `0penBmc`.

---

## 5. Functional Test Execution & Expected Results

### 5.1 Automated Redfish Integration Test Suite

> [!NOTE]
> **Prerequisites**: Ensure the testing PC has `curl` and `jq` installed (`sudo apt-get install -y curl jq`).

Run the regression test suite from your testing machine:

```bash
cd doc/numaker-iot-ma35d03f80/
chmod +x test-redfish.sh
./test-redfish.sh
```

**Expected Execution Output:**
```text
====================================================
     MA35D03F80 OpenBMC Functions Integration Test    
====================================================

[Test] GET Service Root...
✓ Passed (HTTP 200)

[Test] GET Chassis Details (system)...
✓ Passed (HTTP 200)

[Test] GET Chassis ThermalSubsystem...
✓ Passed (HTTP 200)

[Test] User Management (AccountService)...
POST Create Test Account (rftestuser): ✓ Passed (HTTP 201)
PATCH Change Role to ReadOnly: ✓ Passed (HTTP 204)
DELETE Delete Test Account (rftestuser): ✓ Passed (HTTP 200)

====================================================
Test Summary: All Tests Passed!
Report generated: test-redfish.md
====================================================
```

See [`test-redfish.md`](test-redfish.md) for full compliance matrix.

---

### 5.2 Host Serial-Over-LAN (SOL) Console Testing

UART6 (`/dev/ttyS6`) serves as the Host console connection.

1. **Jumper Check**: Verify **J63 Pin 1-2 is shorted** (required for RS-232 mode).
2. **Interactive CLI Access via SSH (Recommended)**:
   ```bash
   ssh -t root@numaker-iot-ma35d03f80.local obmc-console-client
   ```
   *Keystrokes typed in the terminal are transmitted directly to the host UART.*
3. **WebUI Terminal**:
   - In browser: **Operations $\rightarrow$ Serial-over-LAN console**.

> [!NOTE]
> **WebUI SOL Host Power Dependency**:
> OpenBMC's WebUI SOL terminal checks host power status (`PS_PWROK` on `PK12`). If evaluating the board standalone without a connected host, the WebUI terminal displays `System must be powered on to connect`.
> - **Method A (Direct CLI - Recommended)**: Use `ssh -t root@<ip> obmc-console-client`, which connects directly to the serial console server regardless of host power state.
> - **Method B (Hardware Emulation)**: Connect `PK12` to `3.3V`, then click "Power on" in WebUI / Redfish, after which the WebUI terminal connects immediately.

Refer to [`test-sol.md`](test-sol.md) for loopback tests and wiring details.

---

### 5.3 CAN / CAN-FD Bus Testing

MA35D03F80 enables 3 CAN controllers: `can0` (PN2/PN3), `can1` (PN6/PN7), `can2` (PM2/PM3).

> [!WARNING]
> **CAN Transceiver Requirement**:
> The CAN pins on the SoC output 3.3V TTL levels. To connect to a physical CAN bus or another device, an external **3.3V CAN transceiver** (e.g. SN65HVD230 / TJA1051T) with **120Ω termination resistors** on both bus ends is required. Do NOT connect SoC TTL pins directly to a 12V/24V CAN bus.

#### Step 1: Configure CAN Interfaces (e.g. can0 & can1 in CAN-FD mode)
```bash
# In BMC SSH:
ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
ip link set can0 up

ip link set can1 type can bitrate 500000 dbitrate 2000000 fd on
ip link set can1 up
```

#### Step 2: Receive & Transmit Verification
```bash
# Terminal A (Receiver):
candump can1

# Terminal B (Transmitter):
cansend can0 123##3112233445566778899AABBCCDDEEFF
```

**Expected candump output:**
```text
can1  123  [16]  11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF
```

See [`test-can.md`](test-can.md) for complete baudrate matrix and external transceiver wiring diagrams.

---

### 5.4 Host Power Control Testing (GPIO)

| Signal | Direction | Pin | Description |
| :--- | :--- | :--- | :--- |
| **`POWER_OUT`** | Output | **`PN1`** | Emulates power button (Active Low, 200ms on, 4s force off) |
| **`RESET_OUT`** | Output | **`PN0`** | Emulates reset button (Active Low, 200ms) |
| **`PS_PWROK`** | Input | **`PK12`** | Host PSU Power Good status (Active High 3.3V) |

#### Power On Command:
```bash
# Connect PK12 to 3.3V, then issue:
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}' -i
```
**Expected Response:** `HTTP/1.1 204 No Content`

Check host power status:
```bash
curl -k -s -u root:0penBmc https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system | jq .PowerState
```
**Expected Output:** `"On"`

Refer to [`test-power-control.md`](test-power-control.md) for waveform timings and hardware schematics.

---

### 5.5 SoC Temperature Monitoring Verification

Verify the on-die TSEN thermal sensor readings via D-Bus and Redfish:

```bash
# On BMC SSH:
busctl get-property xyz.openbmc_project.MA35_Thermal /xyz/openbmc_project/sensors/temperature/cpu_thermal xyz.openbmc_project.Sensor.Value Value
```
**Expected Output:**
```text
d 42.5
```
*(Indicates CPU temperature is 42.5°C).*

Via Redfish:
```bash
curl -k -s -u root:0penBmc https://numaker-iot-ma35d03f80.local/redfish/v1/Chassis/system/ThermalSubsystem/ThermalMetrics | jq .
```

To run stress & dynamic chart polling test:
```bash
./test-cpu-temp.sh
```

---

## 6. Document Index

- [`test-can.md`](test-can.md): CAN / CAN-FD bus setup, transceiver wiring, and socketCAN commands.
- [`test-sol.md`](test-sol.md): Host SOL console guide, J63 jumper settings, and WebUI integration.
- [`test-redfish.md`](test-redfish.md): Redfish integration test report and schema compliance results.
- [`test-redfish.sh`](test-redfish.sh): Automated curl test script for Redfish API regression tests.
- [`test-power-control.md`](test-power-control.md): Host power state machine, wiring diagrams, and GPIO pinouts.
- [`test-cpu-temp.sh`](test-cpu-temp.sh): Live SoC thermal monitoring and workload stress testing script.
