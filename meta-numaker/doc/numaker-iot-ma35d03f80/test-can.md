# NuMaker-IoT-MA35D03F80 CAN / CAN-FD Guide

## 1. Overview

The MA35D03F80 platform integrates Bosch M_CAN controllers supporting:
- **Classic CAN 2.0A / 2.0B**: 11-bit and 29-bit identifiers, up to 8 bytes payload.
- **CAN-FD**: Extended payload up to 64 bytes with dual bitrates (nominal arbitration + fast data phase).

Three CAN controllers are registered in the Linux SocketCAN subsystem:

| Controller | Base Address | Linux Interface | TX Pin | RX Pin | Pinmux Setting |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`CAN0`** | `0x403C0000` | `can0` | **`PN3`** | **`PN2`** | `PN3MFP_CAN0_TXD` / `PN2MFP_CAN0_RXD` |
| **`CAN1`** | `0x403D0000` | `can1` | **`PN7`** | **`PN6`** | `PN7MFP_CAN1_TXD` / `PN6MFP_CAN1_RXD` |
| **`CAN3`** | `0x403F0000` | `can2` | **`PM3`** | **`PM2`** | `PM3MFP_CAN3_TXD` / `PM2MFP_CAN3_RXD` |

---

## 2. Hardware Signals & Transceiver Wiring

| Signal Name | Direction | Function | MA35 Pin | Electrical |
| :--- | :--- | :--- | :--- | :--- |
| **`CAN0_TXD`** | Output | CAN0 Transmit Data | **`PN3`** | 3.3V TTL |
| **`CAN0_RXD`** | Input | CAN0 Receive Data | **`PN2`** | 3.3V TTL |
| **`CAN1_TXD`** | Output | CAN1 Transmit Data | **`PN7`** | 3.3V TTL |
| **`CAN1_RXD`** | Input | CAN1 Receive Data | **`PN6`** | 3.3V TTL |
| **`CAN3_TXD`** | Output | CAN3 Transmit Data | **`PM3`** | 3.3V TTL |
| **`CAN3_RXD`** | Input | CAN3 Receive Data | **`PM2`** | 3.3V TTL |
| **`GND`** | - | Common Reference Ground | **`GND`** | Common ground reference |

### External Transceiver Wiring

SoC pins output 3.3V TTL. Connect via an external 3.3V CAN transceiver (e.g. SN65HVD230, TJA1051T):

```text
 ┌───────────────────────────┐         ┌────────────────────────┐
 │   NuMaker-IoT-MA35D03F80  │         │  CAN Transceiver (PHY) │
 │                           │         │                        │
 │   CAN_TXD (e.g. PN3/PN7) ─┼────────►│ CAN_TXD          CAN_H ├─────── CAN Bus High
 │   CAN_RXD (e.g. PN2/PN6) ◄┼─────────┤ CAN_RXD          CAN_L ├─────── CAN Bus Low
 │   GND ────────────────────┼─────────┤ GND                GND ├──┬──── Common Ground
 └───────────────────────────┘         └────────────────────────┘  │
                                                                 [120Ω] Termination
                                                                   │
                                                           ────────┴────
```

> [!WARNING]
> Ensure a **120Ω termination resistor** is placed across `CAN_H` and `CAN_L` at each bus end. Do not connect SoC TTL pins directly to 12V/24V bus lines.

---

## 3. Interface Configuration

Always configure bit-timing via `ip link` before enabling an interface. Replace `can0` with the target interface (`can0`, `can1`, or `can2`).

### Mode A: Classic CAN 2.0 (500 kbps)

```bash
ip link set can0 down
ip link set can0 up type can bitrate 500000
ip -details link show can0
```

### Mode B: CAN-FD (500 kbps Nominal + 2 Mbps Data Phase)

```bash
ip link set can0 down
ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
ip -details link show can0
```

### Mode C: Internal Loopback (Self-test without external PHY)

```bash
ip link set can0 down
ip link set can0 up type can bitrate 500000 loopback on
```

---

## 4. Transmission & Reception Testing (`can-utils`)

### 4.1 Two-Port Interconnect Test (`can0` to `can1`)

With `can0` and `can1` wired to the same terminated bus:

```bash
# 1. Bring up both interfaces
ip link set can0 up type can bitrate 500000
ip link set can1 up type can bitrate 500000

# 2. Run listener on can1 in background
candump can1 &

# 3. Transmit test frame from can0
cansend can0 123#1122334455667788
# Expected on can1: can1 123 [8] 11 22 33 44 55 66 77 88
```

### 4.2 Frame Transmission (`cansend`)

```bash
# Standard 11-bit ID
cansend can0 123#1122334455667788

# Extended 29-bit ID
cansend can0 18EAFF00#00EE00

# CAN-FD with Bitrate Switch (BRS, Flags=3) and 64-byte payload
cansend can0 123##30102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F40
```

### 4.3 Traffic Generator (`cangen`)

```bash
# Classic CAN traffic every 50ms (-g 50)
cangen can0 -v -g 50

# CAN-FD traffic with Bitrate Switch (-b) and extended frames (-f)
cangen can0 -v -g 50 -f -b
```

### 4.4 Traffic Monitoring (`candump` / `cansniffer`)

```bash
# Dump raw traffic
candump can0

# Dump with delta timestamps
candump -td -c can0

# Dynamic delta view
cansniffer can0
```

---

## 5. Troubleshooting

1. **`bit-timing not yet defined`**:
   - `ifconfig can0 up` was run without timing parameters. Use `ip link set can0 up type can bitrate <rate>`.

2. **Bus-Off Error (`state BUS-OFF`)**:
   - Usually caused by missing 120Ω termination, mismatched baudrates, or inverted `CAN_H`/`CAN_L`.
   - Enable automatic recovery:
     ```bash
     ip link set can0 type can restart-ms 100
     ```

3. **Check Error Counters & State**:
   ```bash
   ip -details -statistics link show can0
   ```
