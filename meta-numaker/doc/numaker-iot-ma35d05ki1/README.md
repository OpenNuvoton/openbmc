# NuMaker-IoT-MA35D05KI1 OpenBMC User & Operation Guide

This document provides a comprehensive operational guide for developers and engineers to build, flash, verify, and validate all OpenBMC features on the **Nuvoton NuMaker-IoT-MA35D05KI1** evaluation board.

> [!NOTE]
> **What is OpenBMC & System Role**:
> OpenBMC is an open-source Linux distribution for Baseboard Management Controllers (BMCs). In server and edge systems, this evaluation board acts as a **BMC (Management Controller)** to remotely monitor, manage, and recover an external target computer (**Host**). Management tasks are performed out-of-band over the network using DMTF Redfish REST APIs, WebUI, Serial-Over-LAN (SOL) host console routing, and GPIO host power control (`POWER_OUT`, `RESET_OUT`, `PS_PWROK`).

---

## 1. Hardware Specifications & Setup

### 1.1 Specifications

| Item | Detail |
| :--- | :--- |
| **Board** | NuMaker-IoT-MA35D05KI1 |
| **SoC** | Nuvoton MA35D05K (Dual Cortex-A35 @ 650 MHz) |
| **RAM** | 256 MB DDR3L (stacked in MCP) |
| **Storage Support** | **SPI NAND** (512MB), **MicroSD / SD** (SDHCI1) |
| **Debug Console** | UART0 (`/dev/ttyS0`), 115200 8N1 |
| **Host SOL Console** | UART4 (`/dev/ttyS4`), Pins `PI10` (RX) / `PI11` (TX) |
| **CAN Bus** | 4× Bosch M_CAN: CAN0 (`PB10`/`PB11`), CAN1 (`PC6`/`PC7`), CAN2 (`PB12`/`PB13`), CAN3 (`PG8`/`PG9`) |
| **Power Control** | GPIO: `POWER_OUT` (`PN1`), `RESET_OUT` (`PN0`), `PS_PWROK` (`PK12`) |
| **Network** | 10/100M Ethernet (RMII) |
| **Default IP / mDNS** | DHCP or `numaker-iot-ma35d05ki1.local` |
| **Default Credentials** | Username: `root` / Password: `0penBmc` |

### 1.2 Hardware Connectors & Interface Setup

Before getting started, identify the physical connectors on the board:
- **Debug Serial Console (UART0)**: Connect a Micro-USB cable to the board's **VCOM (Virtual COM)** port. Open a serial terminal (PuTTY, Tera Term, or minicom) set to **115200 baud, 8 data bits, no parity, 1 stop bit, no flow control**.
- **NuWriter Programming Port (USB0 Device)**: Connect a Micro-USB cable to the **USB0 (Device)** port when burning firmware. *(Do not connect NuWriter to the VCOM or Host USB ports).*
- **Ethernet Port (LAN)**: Connect an RJ45 Ethernet cable to your local router or switch (DHCP required).
- **Power Port**: Connect 5V power over USB.

### 1.3 Boot Mode DIP Switch Settings (SW2)

The NuMaker-IoT-MA35D05KI1 board provides a 6-position SMD DIP switch (**SW2**) for power-on configuration:

**DIP Switch SW2 Pin Definition (PG0~PG7 internal pull-down):**
- **Switch 1 (`PG0`)**: Secure Boot (ON: Disable, OFF: Enable)
- **Switch 2 (`PG2`)**: Boot Source Select [bit 0]
- **Switch 3 (`PG3`)**: Boot Source Select [bit 1]
- **Switch 4 (`PG4`)**: USB Boot Mode (OFF: USBD Device, ON: USBH Host)
- **Switch 5 (`PG6`)**: SD/eMMC Boot Port (OFF: SD0, ON: SD1)
- **Switch 6 (`HSUSB0_ID`)**: USB0 Role (ON: Device, OFF: Host)

**Power-on Setting:**
- **ON (H)**: Switch set to ON (Pulled UP to 3.3V)
- **OFF (L)**: Switch set to OFF (Internal pull-down to Low)

| Memory Storage | **Burn to** settings (USB Download Mode) | **Boot from** settings (Run Mode) |
| :--- | :--- | :--- |
| **Serial NAND (SPI NAND)**<br>(QSPI0 Flash) | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 2 (PG2) to ON</li><li>Switch 3 (PG3) to ON</li><li>Switch 4 (PG4) to OFF (USBD)</li><li>Switch 5 (PG6) to OFF</li><li>Switch 6 (HSUSB0_ID) to ON</li></ul><br>*(Summary: Switch 1, 2, 3, 6 to ON; 4, 5 to OFF)* | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 2 (PG2) to OFF</li><li>Switch 3 (PG3) to OFF</li><li>Switch 4 (PG4) to OFF</li><li>Switch 5 (PG6) to OFF</li><li>Switch 6 (HSUSB0_ID) to OFF</li></ul><br>*(Summary: Switch 1 to ON; Others to OFF)* |
| **MicroSD Card**<br>(SD1 Slot) | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 2 (PG2) to ON</li><li>Switch 3 (PG3) to ON</li><li>Switch 4 (PG4) to OFF (USBD)</li><li>Switch 5 (PG6) to ON (SD1)</li><li>Switch 6 (HSUSB0_ID) to ON</li></ul><br>*(Summary: Switch 1, 2, 3, 5, 6 to ON; 4 to OFF)* | <ul><li>Switch 1 (PG0) to ON</li><li>Switch 2 (PG2) to ON</li><li>Switch 3 (PG3) to OFF</li><li>Switch 4 (PG4) to OFF</li><li>Switch 5 (PG6) to ON (SD1)</li><li>Switch 6 (HSUSB0_ID) to OFF</li></ul><br>*(Summary: Switch 1, 2, 5 to ON; 3, 4, 6 to OFF)* |

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
MACHINE=numaker-iot-ma35d05ki1 source setup numaker-iot-ma35d05ki1 build-ma35
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

**Build Output Directory:** `build-ma35/tmp/deploy/images/numaker-iot-ma35d05ki1/`

```text
├── nuwriter-pack-spinand-numaker-iot-ma35d05ki1.bin   (SPI NAND image)
├── nuwriter-pack-nand-numaker-iot-ma35d05ki1.bin      (Raw NAND image)
├── nuwriter-pack-sd-numaker-iot-ma35d05ki1.bin        (SD card image)
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
3. In the **Artifacts** section, download `openbmc-numaker-iot-ma35d05ki1.zip`.
4. Extract the zip file to your Windows PC.

---

## 3. Firmware Flashing Procedure (NuWriter)

Flashing on Windows uses Nuvoton's Python-based **NuWriter** tool via command-line batch scripts.

> [!TIP]
> **Flashing Troubleshooting**:
> - **Device Not Detected**: Ensure the board DIP switch (SW2) is set to **USB Download Mode** (Switch 1, 2, 3, 6 to ON; Switch 4, 5 to OFF) and your USB cable is plugged into the **USB0 (Device)** port (not VCOM).
> - **Windows USB Driver**: If NuWriter reports `No USB device found`, open Windows Device Manager and check whether a Nuvoton USB device or WinUSB device is recognized.

### 3.1 Setup (First Time Only)

1. Connect the board's **USB0 (Device)** port to your Windows PC with a USB cable.
2. In the extracted folder, double-click:
   ```cmd
   install_nuwriter.bat
   ```

### 3.2 Flashing to SPI NAND Flash

1. Set the board DIP switch to **USB Boot** mode and power on the board.
2. Run the SPI NAND flashing script:
   ```cmd
   nuwriter_program_spinand.bat
   ```
3. Wait for the confirmation:
   ```text
   Programming completed successfully!
   Reset the board to boot from SPI-NAND.
   ```
4. Power off $\rightarrow$ Set DIP switch to **SPI NAND Boot** $\rightarrow$ Power on.

### 3.3 Flashing to MicroSD Card

1. Insert MicroSD card into the slot. Set board DIP switch (SW2) to **USB Download Mode for SD1** (Switch 1, 2, 3, 5, 6 to ON; Switch 4 to OFF) and power on.
2. Run:
   ```cmd
   nuwriter_program_sd.bat
   ```
3. Power off $\rightarrow$ Set DIP switch (SW2) to **SD Boot** $\rightarrow$ Power on.

---

## 4. Boot Verification & Sanity Checks

### 4.1 Expected Serial Boot Log (UART0, 115200 8N1)

```text
NOTICE:  BL2: v2.8(release):
NOTICE:  BL31: v2.8(release):

U-Boot 2020.07 (Oct 12 2026 - 15:30:00 +0800)
CPU: MA35D05K (Cortex-A35 dual core @ 650 MHz)
DRAM:  256 MiB
NAND:  512 MiB
Loading Kernel from storage...
Starting kernel ...

[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x410fd041]
[    0.000000] Linux version 6.6.93-ma35 (oe-user@oe-host) ...
...
[  OK  ] Started Phosphor Web Server (bmcweb).
[  OK  ] Started MA35 SoC Temperature Monitor (ma35-soc-temp).
[  OK  ] Started Serial-Over-LAN Console Server (obmc-console-server).
[  OK  ] Started Dropbear SSH daemon.

OpenBMC Release 2.14.0-dev
numaker-iot-ma35d05ki1 login:
```

### 4.2 Network & WebUI Access

- **Ping Check:**
  ```bash
  ping -c 3 numaker-iot-ma35d05ki1.local
  ```
  > [!TIP]
  > **IP Address Fallback**: If `.local` does not resolve in your network (e.g. mDNS/multicast is blocked by your router), log into the serial console (UART0) and run `ip addr show eth0` to view the assigned IPv4 address.

- **SSH Access:**
  ```bash
  ssh root@numaker-iot-ma35d05ki1.local
  # Password: 0penBmc
  ```

- **WebUI Browser Access:**
  Open `https://numaker-iot-ma35d05ki1.local/` (or `https://<BMC-IP>/`) in browser.
  > [!NOTE]
  > **Browser HTTPS Security Warning**: OpenBMC uses a self-signed SSL certificate by default. When the browser displays `Your connection is not private` (or `NET::ERR_CERT_AUTHORITY_INVALID`), click **Advanced** and select **Proceed to <ip> (unsafe)** to open the OpenBMC WebUI. Log in with `root` / `0penBmc`.

---

## 5. Functional Test Execution & Expected Results

### 5.1 Automated Redfish Integration Test Suite

> [!NOTE]
> **Prerequisites**: Ensure the testing PC has `curl` and `jq` installed (`sudo apt-get install -y curl jq`).

Run the regression test suite from your testing machine:

```bash
cd doc/numaker-iot-ma35d05ki1/
chmod +x test-redfish.sh
./test-redfish.sh
```

**Expected Execution Output:**
```text
====================================================
     MA35D05KI1 OpenBMC Functions Integration Test    
====================================================

[Test] GET Service Root...
✓ Passed (HTTP 200)

[Test] GET Chassis Details (system)...
✓ Passed (HTTP 200)

[Test] User Management (AccountService)...
POST Create Test Account: ✓ Passed (HTTP 201)
PATCH Change Role: ✓ Passed (HTTP 204)
DELETE Delete Test Account: ✓ Passed (HTTP 200)

====================================================
Test Summary: All Tests Passed!
Report generated: test-redfish.md
====================================================
```

See [`test-redfish.md`](test-redfish.md) for detailed test cases.

---

### 5.2 Host Serial-Over-LAN (SOL) Console Testing

On `numaker-iot-ma35d05ki1`, **`UART4`** (`/dev/ttyS4`, `PI10`/`PI11`) is assigned as the Host SOL link.

1. **Interactive CLI Access via SSH (Recommended)**:
   ```bash
   ssh -t root@numaker-iot-ma35d05ki1.local obmc-console-client
   ```
   *Keystrokes typed in the terminal are transmitted directly to the host UART.*
2. **WebUI Terminal**:
   - Access **Operations $\rightarrow$ Serial-over-LAN console**.

> [!NOTE]
> **WebUI SOL Host Power Dependency**:
> OpenBMC's WebUI SOL terminal checks host power status (`PS_PWROK` on `PK12`). If evaluating the board standalone without a connected host, the WebUI terminal displays `System must be powered on to connect`.
> - **Method A (Direct CLI - Recommended)**: Use `ssh -t root@<ip> obmc-console-client`, which connects directly to the serial console server regardless of host power state.
> - **Method B (Hardware Emulation)**: Connect `PK12` to `3.3V`, then click "Power on" in WebUI / Redfish, after which the WebUI terminal connects immediately.

Refer to [`test-sol.md`](test-sol.md) for loopback wiring and baudrate configuration.

---

### 5.3 CAN / CAN-FD Bus Testing

MA35D05KI1 features 4 CAN controllers: `can0` (PB10/PB11), `can1` (PC6/PC7), `can2` (PB12/PB13), `can3` (PG8/PG9).

> [!WARNING]
> **CAN Transceiver Requirement**:
> The CAN pins on the SoC output 3.3V TTL levels. To connect to a physical CAN bus or another device, an external **3.3V CAN transceiver** (e.g. SN65HVD230 / TJA1051T) with **120Ω termination resistors** on both bus ends is required. Do NOT connect SoC TTL pins directly to a 12V/24V CAN bus.

```bash
# In BMC SSH:
ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
ip link set can0 up

ip link set can1 type can bitrate 500000 dbitrate 2000000 fd on
ip link set can1 up

# Receiver:
candump can1

# Transmitter:
cansend can0 123##3112233445566778899AABBCCDDEEFF
```

See [`test-can.md`](test-can.md) for hardware connection pins and detailed packet formats.

---

### 5.4 Host Power Control Testing (GPIO)

| Signal | Direction | Pin | Description |
| :--- | :--- | :--- | :--- |
| **`POWER_OUT`** | Output | **`PN1`** | Power Button (Active Low, 200ms on, 4s force off) |
| **`RESET_OUT`** | Output | **`PN0`** | Reset Button (Active Low, 200ms) |
| **`PS_PWROK`** | Input | **`PK12`** | Host PSU Power Good status (Active High 3.3V) |

```bash
# Power On Host:
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-ma35d05ki1.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}' -i
```
**Expected Response:** `HTTP/1.1 204 No Content`

Refer to [`test-power-control.md`](test-power-control.md) for full GPIO control guides.

---

### 5.5 SoC Temperature Monitoring

```bash
busctl get-property xyz.openbmc_project.MA35_Thermal /xyz/openbmc_project/sensors/temperature/cpu_thermal xyz.openbmc_project.Sensor.Value Value
```
**Expected Output:** `d <temperature_in_celsius>` (e.g. `d 41.5`).

Via Redfish:
```bash
curl -k -s -u root:0penBmc https://numaker-iot-ma35d05ki1.local/redfish/v1/Chassis/system/ThermalSubsystem/ThermalMetrics | jq .
```

To run stress & dynamic chart polling test:
```bash
./test-cpu-temp.sh
```

---

## 6. Document Index

- [`test-can.md`](test-can.md): CAN / CAN-FD bus setup, transceiver wiring, and socketCAN commands.
- [`test-sol.md`](test-sol.md): Host SOL console guide and WebUI integration.
- [`test-redfish.md`](test-redfish.md): Redfish integration test report and schema compliance results.
- [`test-redfish.sh`](test-redfish.sh): Automated curl test script for Redfish API regression tests.
- [`test-power-control.md`](test-power-control.md): Host power state machine, wiring diagrams, and GPIO pinouts.
- [`test-cpu-temp.sh`](test-cpu-temp.sh): Live SoC thermal monitoring and workload stress testing script.
