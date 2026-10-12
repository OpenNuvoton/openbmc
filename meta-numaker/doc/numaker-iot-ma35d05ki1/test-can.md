# MA35D05K CAN / CAN-FD Bus Guide

## 1. Overview

The NuMaker-IoT-MA35D05KI1 platform integrates four high-performance **Bosch M_CAN** controller capable of supporting both:
- **Classic CAN 2.0A / 2.0B**: Standard 11-bit and extended 29-bit identifiers with up to 8 bytes payload.
- **CAN-FD (Flexible Data-Rate)**: Extended payload up to 64 bytes with dual bitrates (nominal arbitration bitrate + fast data phase bitrate).

On this board, **`CAN3`** (physical base address `0x403F0000`) is enabled and registered as the primary **`can0`** network interface in the Linux SocketCAN subsystem.

---

## 2. Hardware Signal & Pin Definitions

| Signal Name | Direction | Function | MA35 Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`CAN3_RXD`** | Input | CAN Bus Receive Data | **`PG8`** | 3.3V TTL Level |
| **`CAN3_TXD`** | Output | CAN Bus Transmit Data | **`PG9`** | 3.3V TTL Level |
| **`GND`** | - | Common Reference Ground | **`GND`** | Must be connected |

### External CAN Transceiver Wiring
Connect the SoC TTL pins to an external 3.3V CAN transceiver (e.g. SN65HVD230 / TJA1051T / MCP2551 with 3.3V level shift):

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

> ⚠️ **Bus Termination Note**: Ensure a **120Ω termination resistor** is placed across `CAN_H` and `CAN_L` at each end of the CAN bus topology.

---

## 3. Interface Configuration (Bringing Up `can0`)

> ⚠️ **Important**: CAN devices require bit-timing parameters before being enabled. Use `ip link`, not `ifconfig`.

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
ip link set can0 down
ip link set can0 up type can bitrate 500000 loopback on
```

---

## 4. Packet Transmission & Reception Testing (`can-utils`)

The OpenBMC image includes the full `can-utils` suite.

### 1. Sending Frames (`cansend`)

#### ① Classic CAN Standard Frame (11-bit ID)
```bash
# Send standard ID 0x123 with 8 bytes payload
cansend can0 123#1122334455667788

# Send standard ID 0x5AA with 4 bytes payload
cansend can0 5AA#A1B2C3D4
```

#### ② Classic CAN Extended Frame (29-bit ID)
```bash
# Send 29-bit extended ID 0x18EAFF00 with 3 bytes
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

### 2. Continuous Traffic Generator (`cangen`)

Useful for bus load, stability, and throughput testing:

```bash
# Generate continuous Classic CAN traffic every 50ms (-g 50) with verbose output (-v):
cangen can0 -v -g 50

# Generate continuous CAN-FD traffic with Bitrate Switch (-b) and extended payloads (-f):
cangen can0 -v -g 50 -f -b
```
*(Press `Ctrl + C` to stop)*

---

### 3. Monitoring & Dumping Traffic (`candump` & `cansniffer`)

Open a separate terminal window on the BMC to monitor live traffic:

```bash
# Dump all received/transmitted CAN frames in real time:
candump can0

# Dump with delta timestamps and symbolic decoding:
candump -td -c can0

# Interactive dynamic delta view (similar to 'top'):
cansniffer can0
```

---

## 5. Troubleshooting

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
