# MA35D16FJ87C Serial-Over-LAN (SOL) Console Guide

## 1. Overview

On the NuMaker-IoT-MA35D16FJ87C platform, OpenBMC's **Host Serial-Over-LAN (SOL)** link is routed through a dedicated physical UART hardware controller.

On this board, **`UART10`** (registered as `/dev/ttyS10` in Linux) is designated as the Host SOL link. It is fully integrated with:
1. **WebUI SOL Console**: Browser-based interactive terminal via `bmcweb` WebSocket forwarding at `https://<bmc-ip>/#/operations/serial-over-lan`.
2. **SSH / CLI**: Command-line interactive terminal via OpenSSH and `obmc-console-client`.

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Function | MA35 Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`UART10_TXD`** | Output | SOL Transmitter (sends keyboard input to Host UART RX) | **`PH7`** | 3.3V TTL level (J5 header) |
| **`UART10_RXD`** | Input | SOL Receiver (receives data from Host UART TX) | **`PH6`** | 3.3V TTL level (J5 header) |
| **`UART0_TXD`** | Output | BMC Linux Debug Console TX | **`PE14`** | Default 115200 8N1 (VCOM USB) |
| **`UART0_RXD`** | Input | BMC Linux Debug Console RX | **`PE15`** | Default 115200 8N1 (VCOM USB) |
| **`GND`** | - | Common Reference Ground | **`GND`** | Must be connected |

---

## 3. Important Hardware & Software Notes

### ① WebUI SOL Console Power Status Dependency
* **WebUI Protection Logic**: OpenBMC's WebUI frontend (`webui-vue`) verifies host power state before initiating a WebSocket connection. When the host is reported as `Off`, the console displays:
  > `System must be powered on to connect` / `Status: Disconnected`
  and blocks the terminal connection.
* **Power Good Hardware Signal**: The system monitors host power via `x86-power-control` on **`PH2`** (`PS_PWROK`, Active High 3.3V).
* **Workarounds for Standalone Board Evaluation**:
  * **Method A (Hardware Emulation)**: Connect **`PH2`** to **`3.3V`**, then navigate to WebUI: **Operations $\rightarrow$ Server power operations $\rightarrow$ Power on**. Once the state transitions to `On`, the WebUI SOL console connects immediately.
  * **Method B (Direct CLI via SSH — Bypasses Power Check)**: Connect directly from your terminal:
    ```bash
    ssh -t root@<BMC_IP> obmc-console-client
    ```
    This command-line client attaches directly to the serial console server regardless of host power state.

### ② Testing Received Characters (Avoiding Conflict with obmc-console-server)
* **Exclusive Port Ownership**: Upon boot, OpenBMC's `obmc-console-server` daemon holds `/dev/ttyS10` open continuously.
* **Do NOT run `cat /dev/ttyS10`**: Any incoming characters from the serial port are immediately consumed by `obmc-console-server` from the TTY buffer, so `cat` will never capture anything.
* **Proper Verification Methods**:
  * Attach to the interactive console: `obmc-console-client`
  * Or monitor incoming data in real time: `tail -f /var/log/obmc-console.log`

### ③ Serial Communication Parameters
* **Default Settings**: `115200` baud, `8` data bits, `1` stop bit, `No Parity` (8N1).
* **Flow Control**: Hardware flow control is disabled by default (`-crtscts`). Ensure the terminal software on the PC (e.g. Tera Term / PuTTY) has `Flow control` set to **`none`**.

---

## 4. Loopback & Interconnect Wiring Diagram

### 3-Wire Interconnect to Host System
When connecting to a host server's serial port:
```text
  NuMaker-IoT-MA35D16FJ87C (SOL)         Host System COM Port
  UART10_TXD (PH7)  ───────────────────►  RXD
  UART10_RXD (PH6)  ◄───────────────────  TXD
  GND               ───────────────────   GND
```

### Standalone Self-Test (Loopback)
For standalone self-testing without an external host computer, you can connect the board's own **`ttyS0` (BMC Debug Console)** to **`ttyS10` (SOL Console)** in a cross-over loopback configuration using jumper wires:

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                  NuMaker-IoT-MA35D16FJ87C                   │
 │                                                             │
 │   [ ttyS0: BMC Debug Console ]     [ ttyS10: SOL Console ]  │
 │                                                             │
 │   UART0_TXD (PE14) ───────────────► UART10_RXD (PH6)        │
 │   UART0_RXD (PE15) ◄─────────────── UART10_TXD (PH7)        │
 │                                                             │
 │   GND ───────────────────────────── GND                     │
 └─────────────────────────────────────────────────────────────┘
```

> ⚠️ **Important**: UART connections must be **cross-connected** (`TX` $\rightarrow$ `RX`, `RX` $\leftarrow$ `TX`).

---

## 5. Devicetree and Yocto Recipe Configuration

### ① Devicetree (DTS)
`uart10` is configured in `meta-evb-ma35/recipes-kernel/linux/files/ma35d1-iot-ma35d16fj0-v1-512m-bmc.dts`:

```dts
/* Host Serial-Over-LAN (SOL) UART */
&uart10 {
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_uart10>;
    status = "okay";
};

&pinctrl {
    pinctrl_uart10: uart10grp {
        nuvoton,pins =
            <SYS_GPH_MFPL_PH6MFP_UART10_RXD  &pcfg_default>,
            <SYS_GPH_MFPL_PH7MFP_UART10_TXD  &pcfg_default>;
    };
};
```

### ② Yocto Recipe & Service Auto-Enablement
In `meta-evb-ma35/recipes-phosphor/console/obmc-console_%.bbappend`:
- Sets `OBMC_CONSOLE_HOST_TTY:numaker-iot-ma35d16fj87c = "ttyS10"`.
- Installs `server.ttyS10.conf` with `baud = 115200`.
- Creates the systemd symlink in `multi-user.target.wants` to ensure `obmc-console@ttyS10.service` starts automatically at boot.

---

## 6. Testing Guide

### Method A: Testing via WebUI Serial-Over-LAN Console

1. **Access WebUI**:
   - Open your browser and navigate to `https://numaker-iot-ma35d16fj87c.local` (or your BMC's IP).
2. **Navigate to SOL Console**:
   - Go to **Operations** $\rightarrow$ **Serial over LAN console** (`https://<bmc-ip>/#/operations/serial-over-lan`).
3. **Verify Status**:
   - Check that the status shows **Status: Connected** with a green checkmark.
4. **Interactive Verification**:
   - Click inside the dark terminal panel and press the **`Enter`** key.
   - The shell prompt (`numaker-iot login:` or `root@numaker-iot-ma35d16fj87c:~#`) will immediately appear.
   - Type commands (e.g. `ifconfig`, `uname -a`, `top`) to verify seamless, bi-directional serial forwarding.

---

### Method B: Testing via SSH / Command Line

1. **Attach directly via OpenSSH**:
   ```bash
   ssh -t root@numaker-iot-ma35d16fj87c.local obmc-console-client
   ```
   *(To disconnect / detach from the session, type `~.`)*

2. **Inject Test Output from BMC Shell**:
   - From an SSH session on the BMC:
     ```bash
     echo "Hello from ttyS0 to SOL Console!" > /dev/ttyS0
     ```
   - The message will immediately appear in real time on the WebUI SOL console window.

---

## 7. Troubleshooting

1. **Blank screen in WebUI SOL console**:
   - Verify that jumper wires are firmly connected in a cross-over manner (`TX` $\leftrightarrow$ `RX`).
   - Click the black terminal area and press `Enter` to trigger terminal output.
2. **Garbled text or no response**:
   - Verify that `ttyS10` is configured to 115200 baud:
     ```bash
     stty -F /dev/ttyS10
     ```
   - Ensure `/etc/obmc-console/server.ttyS10.conf` contains `baud = 115200`.
3. **Check daemon status**:
   ```bash
   systemctl status obmc-console@ttyS10.service
   ```
