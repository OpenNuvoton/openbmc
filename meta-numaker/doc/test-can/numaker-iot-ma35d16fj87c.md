# MA35D16FJ87C CAN / CAN-FD Bus Guide

## 1. Overview

The NuMaker-IoT-MA35D16FJ87C platform integrates high-performance **Bosch M_CAN** controllers capable of supporting both:
- **Classic CAN 2.0A / 2.0B**: Standard 11-bit and extended 29-bit identifiers with up to 8 bytes payload.
- **CAN-FD (Flexible Data-Rate)**: Extended payload up to 64 bytes with dual bitrates (nominal arbitration bitrate + fast data phase bitrate).

On this platform, **four CAN controllers (`CAN0`, `CAN1`, `CAN2`, `CAN3`)** are enabled in the Devicetree and registered as network interfaces in the Linux SocketCAN subsystem (`can0`, `can1`, `can2`, `can3`):

| Controller | Linux Interface | TX Pin | RX Pin | Pinmux Setting |
| :--- | :--- | :--- | :--- | :--- |
| **`CAN0`** | `can0` | **`PB11`** | **`PB10`** | `SYS_GPB_MFPH_PB11MFP_CAN0_TXD` / `PB10MFP_CAN0_RXD` |
| **`CAN1`** | `can1` | **`PC7`** | **`PC6`** | `SYS_GPC_MFPL_PC7MFP_CAN1_TXD` / `PC6MFP_CAN1_RXD` |
| **`CAN2`** | `can2` | **`PB13`** | **`PB12`** | `SYS_GPB_MFPH_PB13MFP_CAN2_TXD` / `PB12MFP_CAN2_RXD` |
| **`CAN3`** | `can3` | **`PG9`** | **`PG8`** | `SYS_GPG_MFPH_PG9MFP_CAN3_TXD` / `PG8MFP_CAN3_RXD` |

---

## 2. Hardware Signal & Pin Definitions

| Signal Name | Direction | Function | MA35 Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`CAN0_TXD`** | Output | CAN0 Bus Transmit Data | **`PB11`** | 3.3V TTL Level |
| **`CAN0_RXD`** | Input | CAN0 Bus Receive Data | **`PB10`** | 3.3V TTL Level |
| **`CAN1_TXD`** | Output | CAN1 Bus Transmit Data | **`PC7`** | 3.3V TTL Level |
| **`CAN1_RXD`** | Input | CAN1 Bus Receive Data | **`PC6`** | 3.3V TTL Level |
| **`CAN2_TXD`** | Output | CAN2 Bus Transmit Data | **`PB13`** | 3.3V TTL Level |
| **`CAN2_RXD`** | Input | CAN2 Bus Receive Data | **`PB12`** | 3.3V TTL Level |
| **`CAN3_TXD`** | Output | CAN3 Bus Transmit Data | **`PG9`** | 3.3V TTL Level |
| **`CAN3_RXD`** | Input | CAN3 Bus Receive Data | **`PG8`** | 3.3V TTL Level |
| **`GND`** | - | Common Reference Ground | **`GND`** | Must be connected |

### External CAN Transceiver Wiring
Connect the SoC TTL pins to an external 3.3V CAN transceiver (e.g. SN65HVD230 / TJA1051T / MCP2551 with 3.3V level shift):

```text
 ┌───────────────────────────┐         ┌────────────────────────┐
 │ NuMaker-IoT-MA35D16FJ87C  │         │  CAN Transceiver (PHY) │
 │                           │         │                        │
 │   CAN_TXD (e.g. PB11/PC7) ┼────────►│ CAN_TXD          CAN_H ├─────── CAN Bus High
 │   CAN_RXD (e.g. PB10/PC6) ◄┼─────────┤ CAN_RXD          CAN_L ├─────── CAN Bus Low
 │   GND ────────────────────┼─────────┤ GND                GND ├──┬──── Common Ground
 └───────────────────────────┘         └────────────────────────┘  │
                                                                 [120Ω] Termination
                                                                   │
                                                           ────────┴────
```

> ⚠️ **Bus Termination Note**: Ensure a **120Ω termination resistor** is placed across `CAN_H` and `CAN_L` at each end of the CAN bus topology.

---

## 3. Devicetree (DTS) Configuration

In `meta-evb-ma35/recipes-kernel/linux/files/ma35d1-iot-ma35d16fj0-v1-512m-bmc.dts`:

```dts
&can0 {
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_can0>;
    status = "okay";
};

&can1 {
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_can1>;
    status = "okay";
};

&can2 {
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_can2>;
    status = "okay";
};

&can3 {
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_can3>;
    status = "okay";
};

&pinctrl {
    pinctrl_can0: can0grp {
        nuvoton,pins =
            <SYS_GPB_MFPH_PB10MFP_CAN0_RXD  &pcfg_default>,
            <SYS_GPB_MFPH_PB11MFP_CAN0_TXD  &pcfg_default>;
    };

    pinctrl_can1: can1grp {
        nuvoton,pins =
            <SYS_GPC_MFPL_PC6MFP_CAN1_RXD   &pcfg_default>,
            <SYS_GPC_MFPL_PC7MFP_CAN1_TXD   &pcfg_default>;
    };

    pinctrl_can2: can2grp {
        nuvoton,pins =
            <SYS_GPB_MFPH_PB12MFP_CAN2_RXD  &pcfg_default>,
            <SYS_GPB_MFPH_PB13MFP_CAN2_TXD  &pcfg_default>;
    };

    pinctrl_can3: can3grp {
        nuvoton,pins =
            <SYS_GPG_MFPH_PG8MFP_CAN3_RXD   &pcfg_default>,
            <SYS_GPG_MFPH_PG9MFP_CAN3_TXD   &pcfg_default>;
    };
};
```

---

## 4. Interface Configuration (Bringing Up Interfaces)

> ⚠️ **Important**: CAN devices require bit-timing parameters before being enabled. Use `ip link`, not `ifconfig`.
> Replace `<interface>` with `can0`, `can1`, `can2`, or `can3`.

### Mode A: Classic CAN 2.0 (e.g. 500 kbps)

```bash
# 1. Bring down the interface first (if previously up)
ip link set can0 down

# 2. Configure nominal bitrate (e.g. 500000 = 500 kbps) and bring up
ip link set can0 up type can bitrate 500000

# 3. Verify interface state
ip -details link show can0
```

### Mode B: CAN-FD Mode (500 kbps Arbitration + 2 Mbps Data Phase)

```bash
# 1. Bring down the interface
ip link set can0 down

# 2. Configure nominal bitrate, data bitrate, and enable CAN-FD
ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on

# 3. Verify CAN-FD status
ip -details link show can0
```

### Mode C: Internal Loopback Mode (Self-test without external PHY)

For software validation without physical transceiver connected:

```bash
# 1. Bring down the interface
ip link set can0 down

# 2. Enable loopback mode
ip link set can0 up type can bitrate 500000 loopback on
```

---

## 5. Packet Transmission & Reception Testing (`can-utils`)

The OpenBMC image includes the full `can-utils` suite.

### 1. Inter-Channel Communication Test (e.g. `can0` to `can1`)
Connect `CAN0` and `CAN1` through transceivers on the same bus:

1. Bring up both interfaces:
   ```bash
   ip link set can0 up type can bitrate 500000
   ip link set can1 up type can bitrate 500000
   ```
2. Start listener on `can1`:
   ```bash
   candump can1 &
   ```
3. Send test frame from `can0`:
   ```bash
   cansend can0 123#1122334455667788
   ```

### 2. Sending Frames (`cansend`)

#### ① Classic CAN Standard Frame (11-bit ID)
```bash
cansend can0 123#1122334455667788
```

#### ② Classic CAN Extended Frame (29-bit ID)
```bash
cansend can0 18EAFF00#00EE00
```

#### ③ CAN-FD Extended Payload Frame (Up to 64 Bytes)
Syntax for CAN-FD in `cansend`: `<CAN_ID>##<Flags><Data>`  
- `Flags = 0`: Standard CAN-FD frame without Bitrate Switch.
- `Flags = 3`: CAN-FD frame with **Bitrate Switch (BRS)** and **Error State Indicator (ESI)**.

```bash
# Send a 64-byte CAN-FD frame with Bitrate Switch (BRS):
cansend can0 123##30102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F40
```

---

### 3. Continuous Traffic Generator (`cangen`)

Useful for bus load, stability, and throughput testing:

```bash
# Generate continuous Classic CAN traffic every 50ms (-g 50) with verbose output (-v):
cangen can0 -v -g 50

# Generate continuous CAN-FD traffic with Bitrate Switch (-b) and extended payloads (-f):
cangen can0 -v -g 50 -f -b
```
*(Press `Ctrl + C` to stop)*

---

### 4. Monitoring & Dumping Traffic (`candump` & `cansniffer`)

```bash
# Dump all received/transmitted CAN frames in real time:
candump can0

# Dump with delta timestamps and symbolic decoding:
candump -td -c can0

# Interactive dynamic delta view (similar to 'top'):
cansniffer can0
```

---

## 6. Troubleshooting

1. **`SIOCSIFFLAGS: Invalid argument` / `bit-timing not yet defined`**:
   - This occurs if you attempt to use `ifconfig can0 up`.
   - **Solution**: Always use `ip link set can0 up type can bitrate <rate>` to configure timing before bringing up the interface.

2. **Bus-Off Error (`state BUS-OFF`)**:
   - Usually caused by missing termination resistors (120Ω), baud rate mismatch across nodes, or disconnected `CAN_H`/`CAN_L` lines.
   - **Solution**: Check wiring and enable automatic bus-off recovery:
     ```bash
     ip link set can0 type can restart-ms 100
     ```

3. **Check Statistics & Error Counters**:
   ```bash
   ip -details -statistics link show can0
   ```

---

## 7. Verification Results (Mode C: Internal Loopback Mode)

**Date**: 2026-09-16 15:24:57  
**Test Machine**: NuMaker-IoT-MA35D16FJ87C (IP: `192.168.0.138`)  
**Kernel**: Linux 6.6.93-ma35d1-openbmc (aarch64)  

All 4 Bosch M_CAN interfaces (`can0`, `can1`, `can2`, `can3`) successfully verified with internal loopback mode without needing external physical transceivers:

| Interface | Peripheral Base | Classic CAN 500kbps (Standard 11-bit) | Classic CAN 500kbps (Extended 29-bit) | CAN-FD 500k/2M (64-byte Payload + BRS) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`can0`** | `0x403C0000` | ✓ `123 [8] 11 22 33 44 55 66 77 88` | ✓ `18EAFF00 [3] 00 EE 00` | ✓ `123 [64] 01 02 ... 3F 40` | **PASSED** |
| **`can1`** | `0x403D0000` | ✓ `123 [8] 11 22 33 44 55 66 77 88` | ✓ `18EAFF00 [3] 00 EE 00` | ✓ `123 [64] 01 02 ... 3F 40` | **PASSED** |
| **`can2`** | `0x403E0000` | ✓ `123 [8] 11 22 33 44 55 66 77 88` | ✓ `18EAFF00 [3] 00 EE 00` | ✓ `123 [64] 01 02 ... 3F 40` | **PASSED** |
| **`can3`** | `0x403F0000` | ✓ `123 [8] 11 22 33 44 55 66 77 88` | ✓ `18EAFF00 [3] 00 EE 00` | ✓ `123 [64] 01 02 ... 3F 40` | **PASSED** |

