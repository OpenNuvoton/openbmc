# NuMaker-IoT-MA35D03F80 OpenBMC Quickstart & Reference

Operational guide for building, flashing, and verifying OpenBMC on the **Nuvoton NuMaker-IoT-MA35D03F80** evaluation board. The board acts as an out-of-band BMC controlling an external host via Redfish, WebUI, Serial-Over-LAN (SOL), and GPIO power signals (`POWER_OUT`, `RESET_OUT`, `PS_PWROK`).

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
| **Default Credentials** | `root` / `0penBmc` |

### 1.2 Connectors

- **Debug Serial Console (UART0)**: Micro-USB to board **VCOM** port (115200 8N1).
- **NuWriter Programming Port (USB0 Device)**: Micro-USB to board **USB0 (Device)** port. *(Do not connect NuWriter to VCOM or Host USB ports).*
- **Ethernet (LAN)**: RJ45 cable to local network (DHCP).
- **Power**: 5V via USB Type-C connector.

### 1.3 DIP Switch (SW7) & Jumpers

#### Boot Mode Settings (SW7)

SW7 defines boot source and bus configuration at power-on.
- **ON (H)**: Switch ON (3.3V)
- **OFF (L)**: Switch OFF (Pulled down to Low)

**Switch Pin Assignments:**
- `SW1 (PG0)`: Secure Boot (`ON`: Disable, `OFF`: Enable)
- `SW2 (PG1)`: QSPI0 / SD I/O Voltage (`OFF`: 3.3V, `ON`: 1.8V)
- `SW3 (PG2)` / `SW4 (PG3)`: Boot Source (`LL`: QSPI0 Flash, `LH`: SD/eMMC, `HL`: NAND Flash, `HH`: USB)
- `SW5 (PG4)`: USB Boot (`OFF`: USBD Device, `ON`: USBH Host) / NAND Page Size bit 0
- `SW6 (PG5)`: USBH Port (`OFF`: Port 0, `ON`: Port 1) / NAND Page Size bit 1
- `SW7 (PG6)`: QSPI0: SPI-NAND 1-bit / SD: `OFF`=SD0, `ON`=SD1 / NAND BCH bit 0
- `SW8 (PG7)`: QSPI0: `OFF`=SPI-NAND, `ON`=SPI-NOR / SD: `OFF`=4-bit / NAND BCH bit 1

| Target Storage | USB Download (NuWriter) | Normal Boot (Run Mode) |
| :--- | :--- | :--- |
| **SPI NAND** | **1, 3, 4 ON**; others OFF | **1 ON**; others OFF |
| **SD Card (SD1)** | **1, 3, 4, 7 ON**; others OFF | **1, 3, 7 ON**; others OFF |
| **Raw NAND** | **1, 3, 4 ON**; others OFF | **1, 4 ON**; others OFF |

#### Jumper J63 (UART6 RS-232 / RS-485 Selection) — CRITICAL

- **J63 Pin 1-2 MUST BE SHORTED** for Serial-Over-LAN (SOL) RS-232 mode.
- If left open or set to RS-485, the RS-232 transceiver receiver is disconnected, preventing host input.

---

## 2. Build Environment & Compilation

> [!NOTE]
> All build commands below are executed **inside the Docker container**.
> If you have not set up the Docker build environment yet, please refer to [Docker Build Environment Guide](../docker/README.md) to build and enter the container first.

Ensure at least **60 GB** of free disk space for toolchain builds and sstate cache.

### 2.1 Build Steps

1. Inside the Docker container, switch to the OpenBMC repository:
```bash
cd ~/openbmc
```

2. Initialize the build directory:
```bash
MACHINE=numaker-iot-ma35d03f80 source setup numaker-iot-ma35d03f80 build-ma35
```

3. Start compilation:
```bash
bitbake nuwriter-pack
```

> [!NOTE]
> For subsequent sessions in a new shell:
> ```bash
> cd ~/openbmc
> ```
> ```bash
> source oe-init-build-env build-ma35
> ```
> ```bash
> bitbake nuwriter-pack
> ```

### 2.2 Build Outputs

Deploy directory: `build-ma35/tmp/deploy/images/numaker-iot-ma35d03f80/`

```text
├── nuwriter-pack-spinand-numaker-iot-ma35d03f80.bin   (SPI NAND image)
├── nuwriter-pack-nand-numaker-iot-ma35d03f80.bin      (Raw NAND image)
├── nuwriter-pack-sd-numaker-iot-ma35d03f80.bin        (SD card image)
├── install_nuwriter.bat                               (NuWriter environment installer)
├── nuwriter_program_spinand.bat                       (SPI NAND one-click flasher)
├── nuwriter_program_nand.bat                          (Raw NAND one-click flasher)
└── nuwriter_program_sd.bat                            (SD card one-click flasher)
```

### 2.3 Prebuilt Artifacts from GitHub Actions

Precompiled zip packages are available from the CI pipeline:
1. Go to: [OpenBMC GitHub Actions Workflow](https://github.com/OpenNuvoton/openbmc/actions/workflows/numaker.yml).
2. Select the latest successful build.
3. Download `openbmc-numaker-iot-ma35d03f80.zip` from **Artifacts** and extract it on Windows.

---

## 3. Firmware Flashing (NuWriter)

Flashing uses Nuvoton's Python-based **NuWriter** tool via Windows batch scripts.

> [!TIP]
> If NuWriter fails to detect the board:
> - Confirm SW7 is set to **USB Download Mode** (`1, 3, 4 ON`, or `1, 3, 4, 7 ON` for SD1).
> - Verify the cable is connected to **USB0 (Device)**, not VCOM.
> - Check Windows Device Manager for Nuvoton USB / WinUSB driver.

### 3.1 Initial Setup (First Time Only)

1. Connect **USB0 (Device)** to Windows PC.
2. Run `install_nuwriter.bat` in the extracted artifact directory to fetch `MA35D1_NuWriter` and DDR configs.

### 3.2 Flashing SPI NAND

1. Set SW7 to **USB Download Mode** (`1, 3, 4 ON`; others OFF) $\rightarrow$ power on.
2. Run `nuwriter_program_spinand.bat`.
3. Wait for `Programming completed successfully!`.
4. Power off $\rightarrow$ set SW7 to **SPI NAND Boot** (`1 ON`; others OFF) $\rightarrow$ power on.

### 3.3 Flashing Raw NAND

1. Set SW7 to **USB Download Mode** (`1, 3, 4 ON`; others OFF) $\rightarrow$ power on.
2. Run `nuwriter_program_nand.bat`.
3. Wait for completion.
4. Power off $\rightarrow$ set SW7 to **Raw NAND Boot** (`1, 4 ON`; others OFF) $\rightarrow$ power on.

### 3.4 Flashing MicroSD Card

1. Insert MicroSD card into the slot.
2. Set SW7 to **USB Download Mode for SD1** (`1, 3, 4, 7 ON`; others OFF) $\rightarrow$ power on.
3. Run `nuwriter_program_sd.bat`.
4. Power off $\rightarrow$ set SW7 to **SD Boot** (`1, 3, 7 ON`; others OFF) $\rightarrow$ power on.

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

### 4.2 Network & Access

- **mDNS Hostname Resolution**:
  ```bash
  ping -c 3 numaker-iot-ma35d03f80.local
  ```
  *(If mDNS is blocked on your router, log into UART0 and check `ip addr show eth0`).*

- **SSH Access**:
  ```bash
  ssh root@numaker-iot-ma35d03f80.local
  # Password: 0penBmc
  ```

- **WebUI Browser Access**:
  Navigate to `https://numaker-iot-ma35d03f80.local/` (or `https://<BMC-IP>/`).
  Accept the default self-signed SSL certificate in your browser and log in with `root` / `0penBmc`.

---

## 5. Subsystem Verification

### 5.1 Redfish Regression Test Suite

Requires `curl` and `jq` on the test host:

```bash
cd doc/numaker-iot-ma35d03f80/
```

```bash
chmod +x test-redfish.sh
```

```bash
./test-redfish.sh
```

**Output:**
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

See [`test-redfish.md`](test-redfish.md) for full compliance results.

### 5.2 Host Serial-Over-LAN (SOL) Console

UART6 (`/dev/ttyS6`, `PN14`/`PN15`) serves as the Host console connection.

1. **Verify Jumper**: Confirm **J63 Pin 1-2 is shorted** (RS-232 mode).
2. **Interactive CLI Access via SSH (Direct)**:
   ```bash
   ssh -t root@numaker-iot-ma35d03f80.local obmc-console-client
   ```
   *Connects directly to the serial console server regardless of host power state.*
3. **WebUI Terminal**:
   Open **Operations $\rightarrow$ Serial-over-LAN console**.
   > [!NOTE]
   > WebUI terminal checks host power status (`PS_PWROK` on `PK12`). If evaluating standalone without a host motherboard, tie `PK12` to `3.3V` and set Host Power to On via Redfish, or use direct CLI access via `obmc-console-client`.

Refer to [`test-sol.md`](test-sol.md) for loopback tests and wiring diagrams.

### 5.3 CAN / CAN-FD Bus

MA35D03F80 provides 3 CAN controllers: `can0` (`PN2`/`PN3`), `can1` (`PN6`/`PN7`), `can2` (`PM2`/`PM3`).

> [!WARNING]
> SoC CAN pins output 3.3V TTL levels. Connect via an external **3.3V CAN transceiver** (e.g. SN65HVD230 / TJA1051T) with **120Ω termination resistors** on both bus ends. Do NOT connect TTL pins directly to a 12V/24V CAN bus.

Configure `can0` and `can1` for CAN-FD in BMC SSH:
```bash
ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
```

```bash
ip link set can0 up
```

```bash
ip link set can1 type can bitrate 500000 dbitrate 2000000 fd on
```

```bash
ip link set can1 up
```

Terminal A (Receiver):
```bash
candump can1
```

Terminal B (Transmitter):
```bash
cansend can0 123##3112233445566778899AABBCCDDEEFF
```

**Expected candump output:**
```text
can1  123  [16]  11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF
```

See [`test-can.md`](test-can.md) for transceiver schematics and bitrate options.

### 5.4 Host Power Control (GPIO)

| Signal | Direction | Pin | Description |
| :--- | :--- | :--- | :--- |
| **`POWER_OUT`** | Output | **`PN1`** | Emulates power button (Active Low, 200ms on, 4s force off) |
| **`RESET_OUT`** | Output | **`PN0`** | Emulates reset button (Active Low, 200ms) |
| **`PS_PWROK`** | Input | **`PK12`** | Host PSU Power Good status (Active High 3.3V) |

Connect PK12 to 3.3V, then trigger Power On:
```bash
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}' -i
```

Verify power state:
```bash
curl -k -s -u root:0penBmc https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system | jq .PowerState
```

See [`test-power-control.md`](test-power-control.md) for pulse timings and schematics.

### 5.5 SoC Temperature Monitoring

Query on-die TSEN thermal sensor readings via D-Bus (on BMC):
```bash
busctl get-property xyz.openbmc_project.MA35_Thermal /xyz/openbmc_project/sensors/temperature/cpu_thermal xyz.openbmc_project.Sensor.Value Value
```

Via Redfish:
```bash
curl -k -s -u root:0penBmc https://numaker-iot-ma35d03f80.local/redfish/v1/Chassis/system/ThermalSubsystem/ThermalMetrics | jq .
```

Stress and polling test script:
```bash
./test-cpu-temp.sh
```

### 5.6 Firmware Update via Redfish (OTA)

End-to-end Redfish update with dual-bank (A/B) flashing and boot fallback:

```bash
# Automated end-to-end OTA verification (from repo root):
./meta-numaker/doc/numaker-iot-ma35d03f80/test-redfish-update/test-redfish-update.sh numaker-iot-ma35d03f80.local \
  build-ma35/tmp/deploy/images/numaker-iot-ma35d03f80/obmc-phosphor-image-numaker-iot-ma35d03f80.mtd-ubi-tar
```

For partition architecture, manual step-by-step curl commands, anti-rollback checks, and boot fallback testing, refer to [`test-redfish-update/README.md`](test-redfish-update/README.md).

---

## 6. Document Index

- [`test-can.md`](test-can.md): CAN / CAN-FD bus setup, transceiver wiring, and socketCAN commands.
- [`test-sol.md`](test-sol.md): Host SOL console guide, J63 jumper settings, and WebUI integration.
- [`test-redfish.md`](test-redfish.md): Redfish integration test report and schema compliance results.
- [`test-redfish.sh`](test-redfish.sh): Automated curl test script for Redfish API regression tests.
- [`test-redfish-update/README.md`](test-redfish-update/README.md): Redfish OTA firmware update guide, dual-bank architecture, and automated test suite.
- [`test-power-control.md`](test-power-control.md): Host power state machine, wiring diagrams, and GPIO pinouts.
- [`test-cpu-temp.sh`](test-cpu-temp.sh): Live SoC thermal monitoring and workload stress testing script.
