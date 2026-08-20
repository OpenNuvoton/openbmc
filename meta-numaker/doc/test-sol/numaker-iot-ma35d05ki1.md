# MA35D05K Serial-Over-LAN (SOL) Console Guide

## 1. Overview

On the NuMaker-IoT-MA35D05KI1 platform, OpenBMC's **Host Serial-Over-LAN (SOL)** link is routed through a dedicated physical UART hardware controller.

On this board, **`UART4`** (registered as `/dev/ttyS4` in Linux) is designated as the Host SOL link. It is fully integrated with:
1. **WebUI SOL Console**: Browser-based interactive terminal via `bmcweb` WebSocket forwarding at `https://<bmc-ip>/#/operations/serial-over-lan`.
2. **SSH / CLI**: Command-line interactive terminal via OpenSSH and `obmc-console-client`.

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Function | MA35 Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`UART4_RXD`** | Input | SOL Receiver (receives data from Host UART TX) | **`PI10`** | 3.3V TTL level |
| **`UART4_TXD`** | Output | SOL Transmitter (sends keyboard input to Host UART RX) | **`PI11`** | 3.3V TTL level |
| **`UART0_TXD`** | Output | BMC Linux Debug Console TX | **`PB13`** (or Header TX) | Default 115200 8N1 |
| **`UART0_RXD`** | Input | BMC Linux Debug Console RX | **`PB12`** (or Header RX) | Default 115200 8N1 |
| **`GND`** | - | Common Reference Ground | **`GND`** | Must be connected |

---

## 3. Loopback & Interconnect Wiring Diagram

For standalone self-testing without an external host computer, you can connect the board's own **`ttyS0` (BMC Debug Console)** to **`ttyS4` (SOL Console)** in a cross-over loopback configuration using jumper wires:

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                NuMaker-IoT-MA35D05KI1                       │
 │                                                             │
 │   [ ttyS0: BMC Debug Console ]     [ ttyS4: SOL Console ]   │
 │                                                             │
 │   UART0_TXD (PB13) ───────────────► UART4_RXD (PI10)        │
 │   UART0_RXD (PB12) ◄─────────────── UART4_TXD (PI11)        │
 │                                                             │
 │   GND ───────────────────────────── GND                     │
 └─────────────────────────────────────────────────────────────┘
```

> ⚠️ **Important**: UART connections must be **cross-connected** (`TX` $\rightarrow$ `RX`, `RX` $\leftarrow$ `TX`). Do not connect `TX` to `TX`.

---

## 4. Devicetree and Yocto Recipe Configuration

### ① Devicetree (DTS)
`uart4` is enabled in `meta-evb-ma35/recipes-kernel/linux/files/ma35d05k-iot-ma35d05ki1-v1-256m.dts`:

```dts
/* Host Serial-Over-LAN (SOL) UART */
&uart4 {
    status = "okay";
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_uart4>;
};

&pinctrl {
    uart4 {
        pinctrl_uart4: uart4grp {
            nuvoton,pins =
                <SYS_GPI_MFPH_PI10MFP_UART4_RXD    &pcfg_default>,  /* PI10 */
                <SYS_GPI_MFPH_PI11MFP_UART4_TXD    &pcfg_default>;  /* PI11 */
        };
    };
};
```

### ② Yocto Recipe & Service Auto-Enablement
In `meta-evb-ma35/recipes-phosphor/console/obmc-console_%.bbappend`:
- Sets `OBMC_CONSOLE_HOST_TTY = "ttyS4"`.
- Installs `server.ttyS4.conf` with `baud = 115200`.
- Creates the systemd symlink in `multi-user.target.wants` to ensure `obmc-console@ttyS4.service` starts automatically at boot.

---

## 5. Testing Guide

### Method A: Testing via WebUI Serial-Over-LAN Console

1. **Access WebUI**:
   - Open your browser and navigate to `https://192.168.0.89` (or your BMC's IP).
2. **Navigate to SOL Console**:
   - Go to **Operations** $\rightarrow$ **Serial over LAN console** (`https://192.168.0.89/#/operations/serial-over-lan`).
3. **Verify Status**:
   - Check that the status shows **Status: Connected** with a green checkmark.
4. **Interactive Verification**:
   - Click inside the dark terminal panel and press the **`Enter`** key.
   - The shell prompt (`numaker-iot login:` or `root@numaker-iot-ma35d05ki1:~#`) will immediately appear.
   - Type commands (e.g. `ifconfig`, `uname -a`, `top`) to verify seamless, bi-directional serial forwarding.

---

### Method B: Testing via SSH / Command Line

1. **Attach directly via OpenSSH**:
   ```bash
   ssh -t root@192.168.0.89 obmc-console-client
   ```
   *(To disconnect / detach from the session, type `~.`)*

2. **Inject Test Output from BMC Shell**:
   - From an SSH session on the BMC:
     ```bash
     echo "Hello from ttyS0 to SOL Console!" > /dev/ttyS0
     ```
   - The message will immediately appear in real time on the WebUI SOL console window.

---

## 6. Troubleshooting

1. **Blank screen in WebUI SOL console**:
   - Verify that jumper wires are firmly connected in a cross-over manner (`TX` $\leftrightarrow$ `RX`).
   - Click the black terminal area and press `Enter` to trigger terminal output.
2. **Garbled text or no response**:
   - Verify that `ttyS4` is configured to 115200 baud:
     ```bash
     stty -F /dev/ttyS4
     ```
   - Ensure `/etc/obmc-console/server.ttyS4.conf` contains `baud = 115200`.
3. **Check daemon status**:
   ```bash
   systemctl status obmc-console@ttyS4.service
   ```
