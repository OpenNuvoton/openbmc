# MA35D16FJ87C RS-485 Serial Interface (UART12 AUD) Guide

## 1. Overview

On the NuMaker-IoT-MA35D16FJ87C platform, **UART12** is configured as an independent RS-485 serial communication interface with built-in hardware **Auto-Direction (AUD)** control.

In this architecture:
- **`UART10` (`/dev/ttyS10`, PH6/PH7)**: Dedicated as the **Host Serial-Over-LAN (SOL)** console link connected to `obmc-console`.
- **`UART12` (`/dev/ttyS12`, PC13~PC15)**: Dedicated as the **Independent RS-485 Serial Interface** with hardware AUD transceiver direction management.
- **`UART0` (`/dev/ttyS0`, PE14/PE15)**: Dedicated as the **BMC Linux Debug Console**.

---

## 2. Hardware Signal & Pin Definitions

| Signal Name | Direction | Function | Pin | Pinmux Setting | Electrical |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`UART12_nRTS`** | Output | Auto-Direction (AUD) Direction Control | **`PC13`** | `SYS_GPC_MFPH_PC13MFP_UART12_nRTS` | 3.3V TTL to Transceiver DE / /RE |
| **`UART12_RXD`** | Input | RS-485 Receiver Data | **`PC14`** | `SYS_GPC_MFPH_PC14MFP_UART12_RXD` | 3.3V TTL from Transceiver RO |
| **`UART12_TXD`** | Output | RS-485 Transmitter Data | **`PC15`** | `SYS_GPC_MFPH_PC15MFP_UART12_TXD` | 3.3V TTL to Transceiver DI |
| **`GND`** | - | Common Reference Ground | **`GND`** | Board ground | Common ground reference |

---

## 3. Devicetree Configuration

In `meta-numaker/meta-evb-ma35/recipes-kernel/linux/files/ma35d1-iot-ma35d16fj0-v1-512m-bmc.dts`:

```dts
	aliases {
		serial0 = &uart0;
		serial10 = &uart10;
		serial12 = &uart12;
	};

	/* Independent RS-485 Serial Interface with Hardware Auto-Direction (AUD): /dev/ttyS12 (PC13~PC15) */
	&uart12 {
		status = "okay";
		pinctrl-names = "default";
		pinctrl-0 = <&pinctrl_uart12>;
		linux,rs485-enabled-at-boot-time;
		rs485-rts-active-high;
	};

	&pinctrl {
		uart12 {
			pinctrl_uart12: uart12grp{
				nuvoton,pins =
					<SYS_GPC_MFPH_PC13MFP_UART12_nRTS	&pcfg_default>,
					<SYS_GPC_MFPH_PC14MFP_UART12_RXD	&pcfg_default>,
					<SYS_GPC_MFPH_PC15MFP_UART12_TXD	&pcfg_default>;
			};
		};
	};
```

---

## 4. Hardware Auto-Direction (AUD) Operation Principle

Traditional RS-485 communication requires toggling a direction control GPIO pin via software before and after transmitting each frame. This often leads to:
1. Microsecond scheduling delays and bus collisions.
2. Truncation of final stop bits if direction is switched too early.

On the MA35D1 processor:
- The UART controller's built-in **AUD mode** drives the `UART12_nRTS` (PC13) line high immediately when characters are placed into the TX FIFO.
- Once the last stop bit has been physically transmitted on `UART12_TXD` (PC15), the hardware automatically pulls `UART12_nRTS` back to low, immediately re-enabling the receiver.
- This hardware-timed turnaround eliminates userspace timing jitter and driver context-switch latency.

---

## 5. Verification Commands

### ① Check Device Registration
```bash
ls -l /dev/ttyS12
```

### ② Configure Port Speed
```bash
stty -F /dev/ttyS12 115200 cs8 -cstopb -parenb raw -echo
```

### ③ Loopback / Peer Transmission Test
```bash
# In terminal 1 (listener):
cat /dev/ttyS12

# In terminal 2 (sender):
echo "Hello from NuMaker MA35D16FJ87C RS485" > /dev/ttyS12
```
