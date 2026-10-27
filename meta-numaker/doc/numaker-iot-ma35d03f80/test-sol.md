# NuMaker-IoT-MA35D03F80 Serial-Over-LAN (SOL) Console Guide

## 1. Overview

On the NuMaker-IoT-MA35D03F80 platform, OpenBMC's Host Serial-Over-LAN (SOL) link is handled by **`UART6`** (`/dev/ttyS6`), managed by the `obmc-console` daemon at 115200 8N1.

Access methods:
1. **WebUI SOL Console**: Browser terminal via WebSocket at `https://<bmc-ip>/#/operations/serial-over-lan`.
2. **SSH / CLI**: Direct command-line access via `ssh -t root@<bmc-ip> obmc-console-client`.

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Function | Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`UART6_TXD`** | Output | SOL Transmitter (to Host UART RX) | **`PN15`** | 3.3V TTL |
| **`UART6_RXD`** | Input | SOL Receiver (from Host UART TX) | **`PN14`** | 3.3V TTL |
| **`UART6_nRTS`** | Output | Hardware Flow Control RTS | **`PN13`** | 3.3V TTL |
| **`UART6_nCTS`** | Input | Hardware Flow Control CTS | **`PN12`** | 3.3V TTL |
| **`GND`** | - | Common Reference Ground | **`GND`** | Common ground reference |

---

## 3. Hardware Jumpers & Gotchas

### 3.1 Jumper J63 (RS-232 / RS-485 Selection) — CRITICAL

- **J63 PIN 1-2 MUST BE SHORTED** for SOL RS-232 operation.
- This connects the on-board RS-232 transceiver's receiver to MA35D0 `PN14` (`UART6_RXD`).
- If J63 is open or set to RS-485 mode, the receiver line is disconnected. The BMC can transmit data, but host keystrokes cannot be received (kernel logs Framing Errors / Breaks).

### 3.2 WebUI SOL Power Dependency

OpenBMC's WebUI frontend (`webui-vue`) checks host power state before initiating a WebSocket connection. If the host is reported as `Off`, the console displays:
> `System must be powered on to connect` / `Status: Disconnected`

- **For Standalone Board Testing**:
  - **Method A (Direct CLI - Recommended)**:
    ```bash
    ssh -t root@<bmc-ip> obmc-console-client
    ```
    Bypasses the power state check and connects directly to `obmc-console-server`. (Type `~.` to exit).
  - **Method B (Hardware Emulation)**: Tie `PK12` (`PS_PWROK`) to `3.3V`, then trigger Host Power On via WebUI or Redfish.

### 3.3 Exclusive Port Ownership

`obmc-console-server` holds `/dev/ttyS6` open exclusively. Do not run `cat /dev/ttyS6` directly in the shell; incoming characters will be captured by the daemon. Use `obmc-console-client` or monitor `/var/log/obmc-console.log`.

---

## 4. Wiring Diagrams

### 4.1 Connection to Host Server COM Port

```text
  NuMaker-IoT-MA35D03F80 (SOL)           Host System COM Port
  UART6_TXD (PN15)  ───────────────────►  RXD
  UART6_RXD (PN14)  ◄───────────────────  TXD
  UART6_nRTS (PN13) ───────────────────►  CTS
  UART6_nCTS (PN12) ◄───────────────────  RTS
  GND               ───────────────────   GND
```

*Note: TX and RX must be cross-connected.*

### 4.2 Standalone Loopback Self-Test

Connect board debug console `UART0` (`PE14`/`PE15`) to `UART6` (`PN14`/`PN15`) using jumper wires:

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                  NuMaker-IoT-MA35D03F80                     │
 │                                                             │
 │   [ ttyS0: BMC Debug Console ]     [ ttyS6: SOL Console ]   │
 │                                                             │
 │   UART0_TXD (PE14) ───────────────► UART6_RXD (PN14)        │
 │   UART0_RXD (PE15) ◄─────────────── UART6_TXD (PN15)        │
 │   GND ───────────────────────────── GND                     │
 └─────────────────────────────────────────────────────────────┘
```

---

## 5. Verification Steps

### Method A: WebUI Console

1. Navigate to `https://numaker-iot-ma35d03f80.local/#/operations/serial-over-lan`.
2. Confirm status indicates connected.
3. Click inside the terminal and press `Enter` to verify bi-directional serial forwarding.

### Method B: SSH CLI

```bash
# Attach directly to host console
ssh -t root@numaker-iot-ma35d03f80.local obmc-console-client
# Press Enter for shell prompt; exit with ~.
```

To test loopback transmission from BMC:
```bash
echo "Test message to SOL console" > /dev/ttyS0
```

---

## 6. Troubleshooting

1. **Daemon Status**:
   ```bash
   systemctl status obmc-console@ttyS6.service
   ```

2. **Baud Rate Verification**:
   ```bash
   stty -F /dev/ttyS6
   # Configured in /etc/obmc-console/server.ttyS6.conf (default: 115200)
   ```

3. **TX Works, RX Fails (Framing Errors)**:
   - Check jumper **J63 Pin 1-2**. It must be shorted for RS-232 reception.
