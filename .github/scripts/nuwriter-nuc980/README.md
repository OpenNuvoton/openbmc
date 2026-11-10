# NUC980 OpenBMC Deployment

Automated flashing, hardware reset, and boot testing tool for NUC980 OpenBMC prebuilt images.
All deployment scripts, bundled runtime tools, tests, and dependency declarations live here.
The GitHub Actions workflow entry point is [`.github/workflows/deploy-nuc980.yml`](../../workflows/deploy-nuc980.yml).

Python 3.10+ is supported on Linux and Windows. Run the following commands from the OpenBMC repository root:

## 1. Quick Start

```console
# Install Python dependencies
python3 -m pip install -r .github/scripts/nuwriter-nuc980/requirements.txt

# Run test suite
python3 -B -m unittest discover -s .github/scripts/nuwriter-nuc980 -p test_deploy.py -v

# Inspect deployment cases (offline, safe)
python3 .github/scripts/nuwriter-nuc980/deploy.py deploy --list-only --prebuilt-root build-nuc980/tmp/deploy/images/numaker-iot-nuc980g2
```

Tests and `--list-only` require only the standard library. They do not require hardware, USB, UART, or reset jigs.

---

## 2. Directory Layout & Bundled Runtime

Beside `deploy.py`, this directory contains the complete NUC980 NuWriter runtime (`NUC980_PyNuWriter`):
- `nuwriter.py`: NUC980 Python NuWriter CLI and programming backend.
- `sys_cfg/`: DDR configuration files (`NUC980DK71YC.ini`).
- `xusb/`: Target XUSB RAM firmware images (`xusb.bin`, `xusb128.bin`, etc.).
- `ch341_reset_uart.py`: Low-level CH341A USB-to-UART adapter hardware reset generator (RTS active-low pulse).
- `download_hook.py`: Hook to pulse hardware reset and settle USB into NuWriter download mode (`0416:5963`).
- `boot_hook.py`: Hook to pulse hardware reset to boot from freshly flashed media.
- `test_deploy.py`: Deployment unit test suite.
- `requirements.txt`: Python package requirements (`pyusb`, `pyserial`, `pyfdt`).

---

## 3. Supported Machine & Media

- **Target Machine**: `numaker-iot-nuc980g2` (SoC: Nuvoton NUC980DK71YC, 128MB DDR2)
- **Supported Storage Media**:
  | Media | Power-On Setting / DIP Option | Flashing Procedure |
  | :--- | :---: | :--- |
  | `spinand` | `4` | 1. `nuwriter.py -a NUC980DK71YC.ini`<br>2. `nuwriter.py -e spinand all`<br>3. `nuwriter.py --ddr NUC980DK71YC.ini -w spinand nuwriter-pack-spinand-*.bin` |
  | `sd` | `7` | 1. `nuwriter.py -a NUC980DK71YC.ini`<br>2. `nuwriter.py --ddr NUC980DK71YC.ini -w sd nuwriter-pack-sd-*.bin` (or `-w sd 0x0 *.wic`) |

---

## 4. Hardware Configuration & CI Runner Setup

### 4.1 Recommended Setup: Zero-Fixture Pure Software DRAM Boot (方案 1)
- **Board DIP Switch**: **Permanently set to USB Boot (Download Mode)**.
  - No need to flip physical switches between flash and boot phases.
  - Zero hardware relays or multiplexing fixtures required.
- **CH341A Reset Control**: Connect CH341A USB adapter RTS pin to NUC980 `nRESET` pin.
  - Pulses reset before each case to guarantee clean USB download mode entry.
- **Boot Execution Phase**:
  - `deploy.py` automatically resolves the target boot image:
    - **SPI-NAND**: selects `u-boot-spl.bin` (or `u-boot-spl.bin-<machine>`) and executes at SRAM `0x200`. SPL loads `u-boot.bin` from SPI-NAND offset `0x100000` into DDR (`0x00e00000`) and jumps to it.
    - **SD1/eMMC**: selects `u-boot-sd.bin` and executes directly in DDR at `0x00e00000`.
  - NuWriter executes the bootloader via `-w ddr <address> <image> -o execute`.
  - U-Boot loads its environment and boots Linux/OpenBMC directly from the flashed storage medium.

### 4.2 USB and Serial Devices
- **Programming USB**: Connect PC to board **USB (Device)** port (Nuvoton VID:PID `0416:5963`).
- **DUT Console**: Connect PC to board **VCOM** UART port (115200 8N1).
- **CH341A Reset Jig**: Connect CH341A USB adapter RTS pin to NUC980 nRESET pin.

### 4.3 Runner Environment Variables
| Environment Variable | CLI Option | Description |
| :--- | :--- | :--- |
| `NUC980_MACHINE` | `--machine` | Target machine (default: `numaker-iot-nuc980g2`) |
| `NUC980_PREBUILT_ROOT` | `--prebuilt-root` | Extracted prebuilt images directory |
| `NUC980_SERIAL_PORT` | `--serial-port` | DUT UART console device (e.g. `/dev/ttyACM0`) |
| `NUC980_NUWRITER_ROOT` | `--nuwriter-root` | Optional NuWriter runtime directory override |
| `NUC980_BMC_HOST` | `--bmc-host` | BMC mDNS / IP address for post-boot tests |

Validate configuration without resetting or programming hardware:
```console
python3 .github/scripts/nuwriter-nuc980/deploy.py check-runner --serial-port /dev/ttyACM0
```

---

## 5. Boot Sequence & Integration Verification

1. **Phase 1: Download-mode**: Pulses CH341 RTS active-low reset, verifies USB device enumeration (`0416:5963`).
2. **Phase 2: Flash**: Executes NuWriter attach, media erase, and image write sequentially.
3. **Phase 3: Boot**: Pulses CH341 reset, captures UART console stream.
   - Monitors for markers: `U-Boot` -> `Linux version` -> `numaker-iot-nuc980g2 login:`.
   - Aborts on kernel panic, assertion failure, or U-Boot prompt trap.
4. **Phase 4: Post-boot Tests**:
   - Executes `meta-numaker/doc/numaker-iot-nuc980g2/test-redfish.sh` against the BMC host.
5. **Phase 5: Reporting**:
   - Writes `results.json` and `junit.xml` to `autodeploy-results/`.
   - Generates GitHub Step Summary.
