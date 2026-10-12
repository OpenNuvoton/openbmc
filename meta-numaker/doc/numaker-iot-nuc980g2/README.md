# NuMaker-IoT-NUC980G2 OpenBMC User & Operation Guide

This document provides complete instructions for developers and engineers to build, flash, verify, and test the OpenBMC firmware on the **Nuvoton NuMaker-IoT-NUC980G2** evaluation board.

> [!NOTE]
> **What is OpenBMC & System Role**:
> OpenBMC is an open-source Linux distribution for Baseboard Management Controllers (BMCs). In server and edge systems, this evaluation board acts as a **BMC (Management Controller)** to remotely monitor, manage, and recover an external target computer (**Host**). Management tasks are performed out-of-band over the network using DMTF Redfish REST APIs, WebUI, and GPIO host power control (`POWER_OUT`, `RESET_OUT`, `PS_PWROK`).

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
| **Default Credentials** | Username: `root` / Password: `0penBmc` |

### 1.2 Hardware Connectors & Interface Setup

Before getting started, identify the physical connectors on the board:
- **Debug Serial Console (UART0)**: Connect a Micro-USB cable to the board's **VCOM (Virtual COM)** port (or header `PE14`/`PE15`). Open a serial terminal set to **115200 baud, 8 data bits, no parity, 1 stop bit, no flow control**.
- **NuWriter Programming Port (USB Device)**: Connect a Micro-USB cable to the **USB (Device)** port when burning firmware. *(Do not connect NuWriter to the VCOM or Host USB ports).*
- **Ethernet Port (LAN)**: Connect an RJ45 Ethernet cable to your local router or switch (DHCP required).
- **Power Port**: Connect 5V Micro-USB to the dedicated Power port.
- **Boot Mode DIP Switch**:
  - **USB Boot (Download Mode)**: Set DIP switch for USB download when flashing with NuWriter.
  - **SPI NAND Boot (Normal Run Mode)**: Set DIP switch for SPI NAND boot to run OpenBMC.

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
MACHINE=numaker-iot-nuc980g2 source setup numaker-iot-nuc980g2 build-nuc980
bitbake nuwriter-pack
```

> **Note**: For subsequent builds in a new terminal session, execute:
> ```bash
> cd ~/shared/openbmc
> source oe-init-build-env build-nuc980
> bitbake nuwriter-pack
> ```

---

### 2.2 Build Output Directory

**Build Output Directory:** `build-nuc980/tmp/deploy/images/numaker-iot-nuc980g2/`

```text
├── nuwriter-pack-numaker-iot-nuc980g2.bin   (Raw NAND / SPI NAND image)
├── install_nuwriter.bat                     (NuWriter environment installer)
└── nuwriter_program.bat                     (One-click flasher script)
```

---

### 2.3 Downloading Prebuilt Artifacts from GitHub Actions

You can download pre-compiled artifacts directly from GitHub Actions without compiling locally:
1. Navigate to: [OpenBMC building GitHub Actions Workflow](https://github.com/OpenNuvoton/openbmc/actions/workflows/numaker.yml)
2. Select the latest successful workflow run.
3. In the **Artifacts** section, download `openbmc-numaker-iot-nuc980g2.zip`.
4. Extract the zip archive to retrieve `nuwriter-pack.bin`.

---

## 3. Firmware Flashing Procedure (NuWriter)

Tool requirement: [NuWriter for NUC980 (Windows)](https://github.com/OpenNuvoton/NUC980_NuWriter)

> [!TIP]
> **Flashing Troubleshooting**:
> - **Device Not Detected**: Ensure the board DIP switch is set to **USB Boot (Download Mode)** and your USB cable is plugged into the **USB (Device)** port (not VCOM).
> - **Windows USB Driver**: If NuWriter reports `No device connected`, verify that the Nuvoton USB Driver (included in the NuWriter package) is installed in Windows Device Manager.

### Step-by-Step Flashing Procedure:

1. **Hardware Preparation**:
   - Set board DIP switch to **USB Boot** mode.
   - Connect the board's USB Device port to the Windows PC using a USB cable.
   - Power on the board.
2. **Launch NuWriter**:
   - Open `NuWriter.exe`.
   - Ensure the device is recognized as `NUC980`.
   - Select **Target**: `SPI NAND`.
3. **Erase Flash**:
   - Select **Erase** tab $\rightarrow$ Check **Erase All** $\rightarrow$ Click **Erase**.
4. **Program Pack File**:
   - Select **Burn** tab.
   - Set **Type**: `Pack`.
   - Click **Browse** and select `nuwriter-pack.bin`.
   - Click **Burn** and wait for completion (approx. 2-3 minutes).
   - Expected status: `Burn successfully! (100%)`.
5. **Reboot to OpenBMC**:
   - Power off the board.
   - Switch the DIP switch to **SPI NAND Boot** mode.
   - Connect the Serial Console (115200 8N1) and power on the board.

---

## 4. Boot Verification & Sanity Checks

### 4.1 Expected Serial Boot Log

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

### 4.2 Network Verification & WebUI Access

Verify BMC responds to ping and mDNS hostname resolution:

```bash
ping -c 3 numaker-iot-nuc980g2.local
```
> [!TIP]
> **IP Address Fallback**: If `.local` does not resolve in your network (e.g. mDNS/multicast is blocked by your router), log into the serial console (UART0) and run `ip addr show eth0` to view the assigned IPv4 address.

**Expected Output:**
```text
PING numaker-iot-nuc980g2.local (192.168.1.100): 56 data bytes
64 bytes from 192.168.1.100: icmp_seq=0 ttl=64 time=0.812 ms
64 bytes from 192.168.1.100: icmp_seq=1 ttl=64 time=0.745 ms
64 bytes from 192.168.1.100: icmp_seq=2 ttl=64 time=0.789 ms

--- numaker-iot-nuc980g2.local ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
```

SSH Login Verification:
```bash
ssh root@numaker-iot-nuc980g2.local
# Enter password: 0penBmc
```

WebUI Browser Access:
Open `https://numaker-iot-nuc980g2.local/` (or `https://<BMC-IP>/`) in your browser.
> [!NOTE]
> **Browser HTTPS Security Warning**: OpenBMC uses a self-signed SSL certificate by default. When the browser displays `Your connection is not private` (or `NET::ERR_CERT_AUTHORITY_INVALID`), click **Advanced** and select **Proceed to <ip> (unsafe)** to open the OpenBMC WebUI. Log in with `root` / `0penBmc`.

---

## 5. Functional Test Execution & Expected Results

### 5.1 Automated Redfish Integration Test Suite

> [!NOTE]
> **Prerequisites**: Ensure the testing PC has `curl` and `jq` installed (`sudo apt-get install -y curl jq`).

Execute the pre-packaged automated Redfish test script:

```bash
cd doc/numaker-iot-nuc980g2/
chmod +x test-redfish.sh
./test-redfish.sh
```

**Execution Output:**
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
Operator prompted: Connect PF9 to 3.3V (HIGH) for Power On...
POST Host Power On: ✓ Passed (HTTP 204)
GET Verify Host PowerState: ✓ Passed (PowerState=On)

====================================================
Test Summary: All Tests Passed!
Report generated: test-redfish.md
====================================================
```

Detailed test report is saved to [`test-redfish.md`](test-redfish.md).

---

### 5.2 Manual Redfish API Commands & Expected Responses

#### ① Service Root Inspection
```bash
curl -k -s -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/ | jq .
```
**Expected Response (HTTP 200):**
```json
{
  "@odata.id": "/redfish/v1",
  "@odata.type": "#ServiceRoot.v1_15_0.ServiceRoot",
  "AccountService": {
    "@odata.id": "/redfish/v1/AccountService"
  },
  "Chassis": {
    "@odata.id": "/redfish/v1/Chassis"
  },
  "Id": "RootService",
  "Name": "Root Service",
  "RedfishVersion": "1.19.0",
  "Systems": {
    "@odata.id": "/redfish/v1/Systems"
  }
}
```

#### ② Chassis Status & Indicator LED Test
```bash
# Query Chassis
curl -k -s -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/Chassis/system | jq '{Id, Name, Status, PowerState}'
```
**Expected Output (HTTP 200):**
```json
{
  "Id": "system",
  "Name": "system",
  "PowerState": "On",
  "Status": {
    "Health": "OK",
    "State": "Enabled"
  }
}
```

```bash
# Turn ON Location Indicator LED
curl -k -s -u root:0penBmc -X PATCH \
  https://numaker-iot-nuc980g2.local/redfish/v1/Chassis/system \
  -H "Content-Type: application/json" \
  -d '{"LocationIndicatorActive": true}' -i
```
**Expected Response:** `HTTP/1.1 204 No Content` (Board LED illuminates).

---

### 5.3 Host Power Control Testing (GPIO)

NuMaker-IoT-NUC980G2 controls host motherboard power states through `x86-power-control` and `libgpiod`:

| Signal | Direction | Pin | Description |
| :--- | :--- | :--- | :--- |
| **`POWER_OUT`** | Output | **`PD12`** | Power Button (Active Low, 200ms pulse for On, 4s for ForceOff) |
| **`RESET_OUT`** | Output | **`PD13`** | Reset Button (Active Low, 200ms pulse for Reset) |
| **`PS_PWROK`** | Input | **`PF9`** | Power Good input from Host PSU (Active High 3.3V) |

> [!NOTE]
> **Host Power Good (`PS_PWROK` on `PF9`) Requirement**:
> OpenBMC's `x86-power-control` checks host power status on `PF9`. When testing power control commands without a connected host motherboard:
> - **To Power On**: Connect `PF9` to **3.3V** before or immediately after issuing the Power On command.
> - **To Power Off / Force Off**: Disconnect `PF9` (or connect to **GND**) after issuing the Power Off command.

#### Test Step 1: Power On Host
```bash
# Connect PF9 to 3.3V, then issue Power On:
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}' -i
```
**Expected Response:**
```text
HTTP/1.1 204 No Content
```
Verify state changed to `On`:
```bash
curl -k -s -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system | jq .PowerState
```
**Expected Output:** `"On"`

#### Test Step 2: Force Off Host
```bash
# Disconnect PF9 to GND, then issue Force Off:
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceOff"}' -i
```
**Expected Response:** `HTTP/1.1 204 No Content`
Verify state changed to `Off`:
```bash
curl -k -s -u root:0penBmc https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system | jq .PowerState
```
**Expected Output:** `"Off"`

For comprehensive wiring and GPIO mapping details, refer to [`test-power-control.md`](test-power-control.md).

---

## 6. Document Index

The following specific test procedures and test scripts are available in this directory:

- [`test-redfish.md`](test-redfish.md): Full Redfish integration test results and schema compliance matrix.
- [`test-redfish.sh`](test-redfish.sh): Automated curl test script for Redfish regression testing.
- [`test-power-control.md`](test-power-control.md): Wiring diagram, signal timings, and manual GPIO verification guide.
