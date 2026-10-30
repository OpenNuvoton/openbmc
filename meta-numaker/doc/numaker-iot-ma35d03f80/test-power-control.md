# NuMaker-IoT-MA35D03F80 GPIO Power Control Guide

## 1. Overview

The MA35D03F80 BMC controls host power states via GPIO using OpenBMC's `x86-power-control` daemon and `libgpiod`. GPIO lines are addressed by standard line names (`POWER_OUT`, `RESET_OUT`, `PS_PWROK`).

---

## 2. Hardware Signal Definitions

| Signal Name | Direction | Pin | Function | Electrical |
| :--- | :--- | :--- | :--- | :--- |
| **`POWER_OUT`** | Output | **`PN1`** | Emulates ATX power button (200ms on, 4s force off) | Active Low, 3.3V open-drain / push-pull |
| **`RESET_OUT`** | Output | **`PN0`** | Emulates ATX reset button (500ms pulse) | Active Low, 3.3V open-drain / push-pull |
| **`PS_PWROK`** | Input | **`PK12`** | Detects Host PSU Power Good status | Active High, 3.3V input |

### Wiring Diagram

```text
  MA35D03F80 (BMC)               Host Motherboard
  ────────────────               ────────────────
  PN1 (POWER_OUT)  ───────────► PWR_BTN# (power button header)
  PN0 (RESET_OUT)  ───────────► RST_BTN# (reset button header)
  PK12 (PS_PWROK)  ◄─────────── PWROK (ATX PSU / VRM output)
  GND ───────────────────────── GND (common ground)
```

> [!NOTE]
> `POWER_OUT` and `RESET_OUT` idle HIGH (3.3V) and pull LOW when triggered. If evaluating standalone without a host motherboard, tie `PK12` to `3.3V` to simulate Power Good, or to `GND` to simulate power off.

---

## 3. Control Commands

### 3.1 Redfish API

Power On (200ms pulse):
```bash
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}' -i
```

Force Off (4s pulse):
```bash
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceOff"}' -i
```

Graceful Shutdown (short press, OS ACPI handler):
```bash
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "GracefulShutdown"}' -i
```

Force Restart (500ms reset pulse):
```bash
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceRestart"}' -i
```

Query Host Power State:
```bash
curl -k -s -u root:0penBmc \
  https://numaker-iot-ma35d03f80.local/redfish/v1/Systems/system | jq .PowerState
```

### 3.2 D-Bus Commands (BMC SSH)

Query current host power state:
```bash
busctl get-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host CurrentHostState
```

Query current chassis power state:
```bash
busctl get-property xyz.openbmc_project.State.Chassis \
  /xyz/openbmc_project/state/chassis0 \
  xyz.openbmc_project.State.Chassis CurrentPowerState
```

Power On transition:
```bash
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.On"
```

Power Off transition (graceful first, then force off after timeout):
```bash
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.Off"
```

Reboot transition:
```bash
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.Reboot"
```

### 3.3 Low-Level Direct GPIO Control (`gpiod`)

Locate named lines:
```bash
gpiofind POWER_OUT
```

```bash
gpiofind RESET_OUT
```

```bash
gpiofind PS_PWROK
```

Read PS_PWROK status (1=Host on, 0=Host off):
```bash
gpioget $(gpiofind PS_PWROK)
```

Manual 200ms power button pulse:
```bash
gpioset -m time -u 200000 $(gpiofind POWER_OUT)=0
```

Manual 4s force power off pulse:
```bash
gpioset -m time -u 4000000 $(gpiofind POWER_OUT)=0
```

Manual 500ms reset pulse:
```bash
gpioset -m time -u 500000 $(gpiofind RESET_OUT)=0
```

---

## 4. Oscilloscope Verification

### Probe Mapping

- **CH1**: `PN1` (`POWER_OUT`)
- **CH2**: `PN0` (`RESET_OUT`)
- **CH3**: `PK12` (`PS_PWROK`)
- **GND**: BMC Ground
- **Trigger**: Falling edge on CH1 or CH2

### Timing Matrix

| Operation | Trigger Source | Observation Pin | Active Level | Pulse Width |
| :--- | :--- | :--- | :--- | :--- |
| **Power On** | Redfish `On` / D-Bus `Transition.On` | **`PN1`** | LOW | 200 ms |
| **Graceful Shutdown** | Redfish `GracefulShutdown` / D-Bus `Transition.Off` | **`PN1`** | LOW | 200 ms (initial) |
| **Force Off** | Redfish `ForceOff` | **`PN1`** | LOW | 4000 ms |
| **Force Restart** | Redfish `ForceRestart` / D-Bus `Transition.Reboot` | **`PN0`** | LOW | 500 ms |
| **Power Detection** | Query `PowerState` | **`PK12`** | DC level | HIGH=On, LOW=Off |
