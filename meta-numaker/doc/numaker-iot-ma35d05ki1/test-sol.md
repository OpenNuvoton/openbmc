# NuMaker-IoT-MA35D05KI1 Serial-Over-LAN (SOL) Console Guide

## 1. Overview

On the NuMaker-IoT-MA35D05KI1 platform, OpenBMC's Host Serial-Over-LAN (SOL) link is handled by **`UART4`** (`/dev/ttyS4`), managed by the `obmc-console` daemon at 115200 8N1.

Access methods:
1. **WebUI SOL Console**: Browser terminal via WebSocket at `https://<bmc-ip>/#/operations/serial-over-lan`.
2. **SSH / CLI**: Direct command-line access via `ssh -t root@<bmc-ip> obmc-console-client`.

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Function | Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`UART4_RXD`** | Input | SOL Receiver (from Host UART TX) | **`PI10`** | 3.3V TTL |
| **`UART4_TXD`** | Output | SOL Transmitter (to Host UART RX) | **`PI11`** | 3.3V TTL |
| **`GND`** | - | Common Reference Ground | **`GND`** | Common ground reference |

---

## 3. Loopback & Interconnect Wiring

### 3.1 Connection to Host Server COM Port

```text
  NuMaker-IoT-MA35D05KI1 (SOL)           Host System COM Port
  UART4_TXD (PI11)  ───────────────────►  RXD
  UART4_RXD (PI10)  ◄───────────────────  TXD
  GND               ───────────────────   GND
```

*Note: TX and RX must be cross-connected.*

### 3.2 Standalone Loopback Self-Test

Connect board debug console `UART0` (`PE14`/`PE15`) to `UART4` (`PI10`/`PI11`) using jumper wires:

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                NuMaker-IoT-MA35D05KI1                       │
 │                                                             │
 │   [ ttyS0: BMC Debug Console ]     [ ttyS4: SOL Console ]   │
 │                                                             │
 │   UART0_TXD (PE14) ───────────────► UART4_RXD (PI10)        │
 │   UART0_RXD (PE15) ◄─────────────── UART4_TXD (PI11)        │
 │   GND ───────────────────────────── GND                     │
 └─────────────────────────────────────────────────────────────┘
```

---

## 4. Verification Steps

### Method A: WebUI Console

1. Navigate to `https://numaker-iot-ma35d05ki1.local/#/operations/serial-over-lan`.
2. Confirm status indicates connected.
3. Click inside the terminal and press `Enter` to verify bi-directional serial forwarding.

### Method B: SSH CLI

```bash
# Attach directly to host console
ssh -t root@numaker-iot-ma35d05ki1.local obmc-console-client
# Press Enter for shell prompt; exit with ~.
```

To test loopback transmission from BMC:
```bash
echo "Test message to SOL console" > /dev/ttyS0
```

---

## 5. Troubleshooting

1. **Daemon Status**:
   ```bash
   systemctl status obmc-console@ttyS4.service
   ```

2. **Baud Rate Verification**:
   ```bash
   stty -F /dev/ttyS4
   # Configured in /etc/obmc-console/server.ttyS4.conf (default: 115200)
   ```

3. **Check Cross-Connection**:
   Ensure `UART0_TXD` connects to `UART4_RXD` (`PI10`) and `UART0_RXD` connects to `UART4_TXD` (`PI11`).
