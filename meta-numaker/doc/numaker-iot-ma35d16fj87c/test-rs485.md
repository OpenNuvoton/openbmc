# NuMaker-IoT-MA35D16FJ87C RS-485 Serial Interface (UART12 AUD) Guide

## 1. Overview

On the NuMaker-IoT-MA35D16FJ87C platform, **UART12** (`/dev/ttyS12`) operates as an independent RS-485 serial communication interface with hardware **Auto-Direction (AUD)** control.

UART Role Assignments:
- **`UART0` (`/dev/ttyS0`, `PE14`/`PE15`)**: BMC Linux Debug Console.
- **`UART10` (`/dev/ttyS10`, `PH6`/`PH7`)**: Host Serial-Over-LAN (SOL) console link connected to `obmc-console`.
- **`UART12` (`/dev/ttyS12`, `PC13`~`PC15`)**: Independent RS-485 interface with hardware transceiver direction control.

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Function | Pin | Electrical |
| :--- | :--- | :--- | :--- | :--- |
| **`UART12_nRTS`** | Output | Auto-Direction (AUD) Direction Control | **`PC13`** | 3.3V TTL to Transceiver DE / /RE |
| **`UART12_RXD`** | Input | RS-485 Receiver Data | **`PC14`** | 3.3V TTL from Transceiver RO |
| **`UART12_TXD`** | Output | RS-485 Transmitter Data | **`PC15`** | 3.3V TTL to Transceiver DI |
| **`GND`** | - | Common Reference Ground | **`GND`** | Common ground reference |

---

## 3. Hardware Auto-Direction (AUD) Operation Principle

Software-driven GPIO direction control introduces scheduler latency and risk of truncating stop bits.
On the MA35D1:
- The UART controller's built-in **AUD mode** drives `UART12_nRTS` (`PC13`) high automatically when data enters the TX FIFO.
- As soon as the final stop bit finishes transmitting on `UART12_TXD` (`PC15`), the controller pulls `UART12_nRTS` low, immediately releasing the bus for reception.
- This turnaround is handled at wire speed without userspace or kernel interrupt latency.

---

## 4. Verification Commands

### 4.1 Device Node Check

```bash
ls -l /dev/ttyS12
```

### 4.2 Port Configuration

```bash
stty -F /dev/ttyS12 115200 cs8 -cstopb -parenb raw -echo
```

### 4.3 Send & Receive Test

```bash
# Terminal 1 (Receiver):
cat /dev/ttyS12

# Terminal 2 (Transmitter):
echo "Hello from NuMaker MA35D16FJ87C RS485" > /dev/ttyS12
```
