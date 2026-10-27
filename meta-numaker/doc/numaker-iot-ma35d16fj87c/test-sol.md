# NuMaker-IoT-MA35D16FJ87C Serial-Over-LAN (SOL) Console Guide

## 1. Overview

On the NuMaker-IoT-MA35D16FJ87C platform, OpenBMC's Host Serial-Over-LAN (SOL) link is handled by **`UART10`** (`/dev/ttyS10`), managed by the `obmc-console` daemon at 115200 8N1.

Access methods:
1. **WebUI SOL Console**: Browser terminal via WebSocket at `https://<bmc-ip>/#/operations/serial-over-lan`.
2. **SSH / CLI**: Direct command-line access via `ssh -t root@<bmc-ip> obmc-console-client`.

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Function | Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`UART10_RXD`** | Input | SOL Receiver (from Host UART TX) | **`PH6`** | 3.3V TTL |
| **`UART10_TXD`** | Output | SOL Transmitter (to Host UART RX) | **`PH7`** | 3.3V TTL |
| **`GND`** | - | Common Reference Ground | **`GND`** | Common ground reference |

---

## 3. Important Notes

### 3.1 WebUI SOL Power Dependency

OpenBMC's WebUI frontend (`webui-vue`) checks host power state before initiating a WebSocket connection. If the host is reported as `Off`, the console displays:
> `System must be powered on to connect` / `Status: Disconnected`

- **For Standalone Board Testing**:
  - **Method A (Direct CLI - Recommended)**:
    ```bash
    ssh -t root@<bmc-ip> obmc-console-client
    ```
    Bypasses the power check and connects directly to `obmc-console-server`. (Type `~.` to exit).
  - **Method B (Hardware Emulation)**: Tie `PK12` (`PS_PWROK`) to `3.3V`, then trigger Host Power On via WebUI or Redfish.

### 3.2 Exclusive Port Ownership

`obmc-console-server` holds `/dev/ttyS10` open exclusively. Do not run `cat /dev/ttyS10` directly in the shell; incoming characters will be captured by the daemon. Use `obmc-console-client` or monitor `/var/log/obmc-console.log`.

---

## 4. Wiring Diagrams

### 4.1 Connection to Host Server COM Port

```text
  NuMaker-IoT-MA35D16FJ87C (SOL)         Host System COM Port
  UART10_TXD (PH7)  ───────────────────►  RXD
  UART10_RXD (PH6)  ◄───────────────────  TXD
  GND               ───────────────────   GND
```

*Note: TX and RX must be cross-connected.*

### 4.2 Standalone Loopback Self-Test

Connect board debug console `UART0` (`PE14`/`PE15`) to `UART10` (`PH6`/`PH7`) using jumper wires:

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                  NuMaker-IoT-MA35D16FJ87C                   │
 │                                                             │
 │   [ ttyS0: BMC Debug Console ]     [ ttyS10: SOL Console ]  │
 │                                                             │
 │   UART0_TXD (PE14) ───────────────► UART10_RXD (PH6)        │
 │   UART0_RXD (PE15) ◄─────────────── UART10_TXD (PH7)        │
 │   GND ───────────────────────────── GND                     │
 └─────────────────────────────────────────────────────────────┘
```

---

## 5. Verification Steps

### Method A: WebUI Console

1. Navigate to `https://numaker-iot-ma35d16fj87c.local/#/operations/serial-over-lan`.
2. Confirm status indicates connected.
3. Click inside the terminal and press `Enter` to verify bi-directional serial forwarding.

### Method B: SSH CLI

```bash
# Attach directly to host console
ssh -t root@numaker-iot-ma35d16fj87c.local obmc-console-client
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
   systemctl status obmc-console@ttyS10.service
   ```

2. **Baud Rate Verification**:
   ```bash
   stty -F /dev/ttyS10
   # Configured in /etc/obmc-console/server.ttyS10.conf (default: 115200)
   ```

3. **Check Cross-Connection**:
   Ensure `UART0_TXD` connects to `UART10_RXD` (`PH6`) and `UART0_RXD` connects to `UART10_TXD` (`PH7`).
