# MA35D03F80 Serial-Over-LAN (SOL) Console Guide

## 1. Overview

On the NuMaker-IoT-MA35D03F80 platform, OpenBMC's **Host Serial-Over-LAN (SOL)** link is routed through a dedicated physical UART hardware controller.

On this board, **`UART6`** (registered as `/dev/ttyS6` in Linux) is designated as the Host SOL link. It is fully integrated with:
1. **WebUI SOL Console**: Browser-based interactive terminal via `bmcweb` WebSocket forwarding at `https://<bmc-ip>/#/operations/serial-over-lan`.
2. **SSH / CLI**: Command-line interactive terminal via OpenSSH and `obmc-console-client`.

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Function | MA35 Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`UART6_TXD`** | Output | SOL Transmitter (sends keyboard input to Host UART RX) | **`PN15`** | 3.3V TTL level |
| **`UART6_RXD`** | Input | SOL Receiver (receives data from Host UART TX) | **`PN14`** | 3.3V TTL level |
| **`UART6_nRTS`** | Output | SOL Request To Send (hardware flow control output) | **`PN13`** | 3.3V TTL level |
| **`UART6_nCTS`** | Input | SOL Clear To Send (hardware flow control input) | **`PN12`** | 3.3V TTL level |
| **`UART0_TXD`** | Output | BMC Linux Debug Console TX | **`PE14`** (or Header TX) | Default 115200 8N1 |
| **`UART0_RXD`** | Input | BMC Linux Debug Console RX | **`PE15`** (or Header RX) | Default 115200 8N1 |
| **`GND`** | - | Common Reference Ground | **`GND`** | Must be connected |

---

## 3. Important Hardware & Software Notes

### ① Hardware Jumper J63 Configuration (RS-232 / RS-485 Selection) — CRITICAL ⚠️
* **Board Architecture**: The NuMaker-IoT-MA35D03F80 board shares `UART6` between on-board RS-232 and RS-485 transceiver circuits.
* **RS-232 Mode (Required for SOL)**:
  * **Jumper J63 PIN 1 and PIN 2 MUST be shorted (Jumper on 1-2)**.
  * This routes the RS-232 transceiver's receiver output directly to MA35D0 **`PN14` (`UART6_RXD`)**.
* **Symptom if not shorted**:
  * If J63 is open or set to RS-485 mode, `UART6_RXD` is disconnected from the RS-232 receiver.
  * **Behavior**: BMC transmits cleanly (TX works), but any input sent from the host/PC cannot be received (kernel records continuous Framing Errors and Breaks, `fe` and `brk` counters increment).

### ② WebUI SOL Console Power Status Dependency
* **WebUI Protection Logic**: OpenBMC's WebUI frontend (`webui-vue`) verifies host power state before initiating a WebSocket connection. When the host is reported as `Off`, the console displays:
  > `System must be powered on to connect` / `Status: Disconnected`
  and blocks the terminal connection.
* **Power Good Hardware Signal**: The system monitors host power via `x86-power-control` on **`PK12`** (`PS_PWROK`, Active High 3.3V).
* **Workarounds for Standalone Board Evaluation**:
  * **Method A (Hardware Emulation)**: Connect **`PK12`** to **`3.3V`**, then navigate to WebUI: **Operations $\rightarrow$ Server power operations $\rightarrow$ Power on**. Once the state transitions to `On`, the WebUI SOL console connects immediately.
  * **Method B (Direct CLI via SSH — Bypasses Power Check)**: Connect directly from your terminal:
    ```bash
    ssh -t root@<BMC_IP> obmc-console-client
    ```
    This command-line client attaches directly to the serial console server regardless of host power state.

### ③ Testing Received Characters (Avoiding Conflict with obmc-console-server)
* **Exclusive Port Ownership**: Upon boot, OpenBMC's `obmc-console-server` daemon holds `/dev/ttyS6` open continuously.
* **Do NOT run `cat /dev/ttyS6`**: Any incoming characters from the serial port are immediately consumed by `obmc-console-server` from the TTY buffer, so `cat` will never capture anything.
* **Proper Verification Methods**:
  * Attach to the interactive console: `obmc-console-client`
  * Or monitor incoming data in real time: `tail -f /var/log/obmc-console.log`

### ④ Serial Communication Parameters
* **Default Settings**: `115200` baud, `8` data bits, `1` stop bit, `No Parity` (8N1).
* **Flow Control**: Hardware flow control is disabled by default (`-crtscts`). Ensure the terminal software on the PC (e.g. Tera Term / PuTTY) has `Flow control` set to **`none`**.

---

## 4. Loopback & Interconnect Wiring Diagram


### 5-Wire Interconnect to Host System
When connecting to a host server's 5-wire serial port:
```text
  NuMaker-IoT-MA35D03F80 (SOL)           Host System COM Port
  UART6_TXD (PN15)  ───────────────────►  RXD
  UART6_RXD (PN14)  ◄───────────────────  TXD
  UART6_nRTS (PN13) ───────────────────►  CTS
  UART6_nCTS (PN12) ◄───────────────────  RTS
  GND               ───────────────────   GND
```

### Standalone Self-Test (Loopback)
For standalone self-testing without an external host computer, you can connect the board's own **`ttyS0` (BMC Debug Console)** to **`ttyS6` (SOL Console)** in a cross-over loopback configuration using jumper wires:

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                  NuMaker-IoT-MA35D03F80                     │
 │                                                             │
 │   [ ttyS0: BMC Debug Console ]     [ ttyS6: SOL Console ]   │
 │                                                             │
 │   UART0_TXD (PE14) ───────────────► UART6_RXD (PN14)        │
 │   UART0_RXD (PE15) ◄─────────────── UART6_TXD (PN15)        │
 │                                                             │
 │   GND ───────────────────────────── GND                     │
 └─────────────────────────────────────────────────────────────┘
```

> ⚠️ **Important**: UART connections must be **cross-connected** (`TX` $\rightarrow$ `RX`, `RX` $\leftarrow$ `TX`, `RTS` $\rightarrow$ `CTS`, `CTS` $\leftarrow$ `RTS`).

---

## 5. Devicetree and Yocto Recipe Configuration

### ① Devicetree (DTS)
`uart6` is configured with all 4 signals (5-wire including GND) in `meta-evb-ma35/recipes-kernel/linux/files/ma35d0-iot-256m-bmc.dts`:

```dts
/* Host Serial-Over-LAN (SOL) UART */
&uart6 {
    status = "okay";
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_uart6>;
};

&pinctrl {
    uart6 {
        pinctrl_uart6: uart6grp {
            nuvoton,pins =
                <SYS_GPN_MFPH_PN12MFP_UART6_nCTS   &pcfg_default>,  /* PN12: nCTS */
                <SYS_GPN_MFPH_PN13MFP_UART6_nRTS   &pcfg_default>,  /* PN13: nRTS */
                <SYS_GPN_MFPH_PN14MFP_UART6_RXD    &pcfg_default>,  /* PN14: RXD */
                <SYS_GPN_MFPH_PN15MFP_UART6_TXD    &pcfg_default>;  /* PN15: TXD */
        };
    };
};
```

### ② Yocto Recipe & Service Auto-Enablement
In `meta-evb-ma35/recipes-phosphor/console/obmc-console_%.bbappend`:
- Sets `OBMC_CONSOLE_HOST_TTY:numaker-iot-ma35d03f80 = "ttyS6"`.
- Installs `server.ttyS6.conf` with `baud = 115200`.
- Creates the systemd symlink in `multi-user.target.wants` to ensure `obmc-console@ttyS6.service` starts automatically at boot.

---

## 6. Testing Guide

### Method A: Testing via WebUI Serial-Over-LAN Console

1. **Access WebUI**:
   - Open your browser and navigate to `https://numaker-iot-ma35d03f80.local` (or your BMC's IP).
2. **Navigate to SOL Console**:
   - Go to **Operations** $\rightarrow$ **Serial over LAN console** (`https://<bmc-ip>/#/operations/serial-over-lan`).
3. **Verify Status**:
   - Check that the status shows **Status: Connected** with a green checkmark.
4. **Interactive Verification**:
   - Click inside the dark terminal panel and press the **`Enter`** key.
   - The shell prompt (`numaker-iot login:` or `root@numaker-iot-ma35d03f80:~#`) will immediately appear.
   - Type commands (e.g. `ifconfig`, `uname -a`, `top`) to verify seamless, bi-directional serial forwarding.

---

### Method B: Testing via SSH / Command Line

1. **Attach directly via OpenSSH**:
   ```bash
   ssh -t root@numaker-iot-ma35d03f80.local obmc-console-client
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
   - Verify that `ttyS6` is configured to 115200 baud:
     ```bash
     stty -F /dev/ttyS6
     ```
   - Ensure `/etc/obmc-console/server.ttyS6.conf` contains `baud = 115200`.
3. **Check daemon status**:
   ```bash
   systemctl status obmc-console@ttyS6.service
   ```
4. **Can transmit but cannot receive (Framing Error / Break)**:
   - Ensure jumper **J63 Pin 1 and Pin 2 are shorted** to route the RS-232 transceiver's RX output to `UART6_RXD` (`PN14`).
   - If J63 is open, the receiver line floats or is switched to RS-485, causing continuous framing errors or silent drop.

