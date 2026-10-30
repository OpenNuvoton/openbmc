# NuMaker-IoT-MA35D05KI1 CAN / CAN-FD Guide

## 1. Overview

The MA35D05KI1 platform integrates Bosch M_CAN controllers supporting:
- **Classic CAN 2.0A / 2.0B**: 11-bit and 29-bit identifiers, up to 8 bytes payload.
- **CAN-FD**: Extended payload up to 64 bytes with dual bitrates (nominal arbitration + fast data phase).

On this board, **`CAN3`** (`0x403F0000`) is registered as **`can0`** in Linux:

| Controller | Base Address | Linux Interface | TX Pin | RX Pin | Electrical |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`CAN3`** | `0x403F0000` | `can0` | **`PG9`** | **`PG8`** | 3.3V TTL |

---

## 2. Hardware Signals & Transceiver Wiring

| Signal Name | Direction | Function | Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`CAN3_TXD`** | Output | CAN Bus Transmit Data | **`PG9`** | 3.3V TTL |
| **`CAN3_RXD`** | Input | CAN Bus Receive Data | **`PG8`** | 3.3V TTL |
| **`GND`** | - | Common Reference Ground | **`GND`** | Common ground reference |

### External Transceiver Wiring

SoC pins output 3.3V TTL. Connect via an external 3.3V CAN transceiver (e.g. SN65HVD230, TJA1051T):

```text
 ┌───────────────────────────┐         ┌────────────────────────┐
 │   NuMaker-IoT-MA35D05KI1  │         │  CAN Transceiver (PHY) │
 │                           │         │                        │
 │   PG9 (CAN3_TXD) ─────────┼────────►│ CAN_TXD          CAN_H ├─────── CAN Bus High
 │   PG8 (CAN3_RXD) ◄────────┼─────────┤ CAN_RXD          CAN_L ├─────── CAN Bus Low
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

Always configure bit-timing via `ip link` before enabling an interface:

### Mode A: Classic CAN 2.0 (500 kbps)

```bash
ip link set can0 down
```

```bash
ip link set can0 up type can bitrate 500000
```

```bash
ip -details link show can0
```

### Mode B: CAN-FD (500 kbps Nominal + 2 Mbps Data Phase)

```bash
ip link set can0 down
```

```bash
ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
```

```bash
ip -details link show can0
```

### Mode C: Internal Loopback (Self-test without external PHY)

```bash
ip link set can0 down
```

```bash
ip link set can0 up type can bitrate 500000 loopback on
```

---

## 4. Transmission & Reception Testing (`can-utils`)

### 4.1 Frame Transmission (`cansend`)

Standard 11-bit ID:
```bash
cansend can0 123#1122334455667788
```

Extended 29-bit ID:
```bash
cansend can0 18EAFF00#00EE00
```

CAN-FD with Bitrate Switch (BRS, Flags=3) and 64-byte payload:
```bash
cansend can0 123##30102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F40
```

### 4.2 Traffic Generator (`cangen`)

Classic CAN traffic every 50ms (-g 50):
```bash
cangen can0 -v -g 50
```

CAN-FD traffic with Bitrate Switch (-b) and extended frames (-f):
```bash
cangen can0 -v -g 50 -f -b
```

### 4.3 Traffic Monitoring (`candump` / `cansniffer`)

Dump raw traffic:
```bash
candump can0
```

Dump with delta timestamps:
```bash
candump -td -c can0
```

Dynamic delta view:
```bash
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
