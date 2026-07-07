# MA35D0 GPIO Power Control

## Overview

NuMaker-IoT-MA35D0 serves as a BMC (Dual Cortex-A35, 256MB DDR), controlling the Host power via GPIO.
It uses OpenBMC's `x86-power-control` daemon with `libgpiod` to operate GPIO lines by name.

## Hardware Signal Definitions

| Signal Name | Direction | Function | Pin | GPIO Port |
|-------------|-----------|----------|-----|-----------|
| `POWER_OUT` | Output | Emulates ATX power button (200ms=power on, 4s=force off) | PN1 | gpion, line 1 |
| `RESET_OUT` | Output | Emulates reset button (pull low for 500ms) | PN0 | gpion, line 0 |
| `PS_PWROK` | Input | Detects Host PSU Power Good | PK12 | gpiok, line 12 |

## Wiring Diagram

```
MA35D0 (BMC)                   Host Motherboard
────────────                   ────────────────
PN1 (POWER_OUT)  ─────────── PWR_BTN# (power button header)
PN0 (RESET_OUT)  ─────────── RST_BTN# (reset button header)
PK12 (PS_PWROK)  ◄────────── PWROK (ATX PSU / VRM output)
GND ──────────────────────── GND (common ground)
```

> **Electrical Specs**: MA35D0 GPIO is 3.3V. POWER_OUT/RESET_OUT are active-low (Host side has pull-up resistors). PS_PWROK is active-high input.

## DTS Configuration

GPIO line names are defined in `ma35d0-iot-256m-bmc.dts`:

```dts
&gpion {
    gpio-line-names =
        "RESET_OUT",    /* PN0 */
        "POWER_OUT";    /* PN1 */
};

&gpiok {
    gpio-line-names =
        "","","","","","","","","","","","",
        "PS_PWROK";     /* PK12 */
};
```

## power-config-host0.json

```json
{
    "gpio_configs": [
        {
            "Name": "PowerOut",
            "LineName": "POWER_OUT",
            "Type": "GPIO",
            "Polarity": "ActiveLow"
        },
        {
            "Name": "PowerOk",
            "LineName": "PS_PWROK",
            "Type": "GPIO",
            "Polarity": "ActiveHigh"
        },
        {
            "Name": "ResetOut",
            "LineName": "RESET_OUT",
            "Type": "GPIO",
            "Polarity": "ActiveLow"
        }
    ],
    "timing_configs": {
        "PowerPulseMs": 200,
        "ForceOffPulseMs": 4000,
        "ResetPulseMs": 500,
        "PowerOkWatchdogMs": 8000,
        "GracefulPowerOffS": 300,
        "WarmResetCheckMs": 500
    }
}
```

## Commands

### Redfish API

```bash
# Power On (short press 200ms)
curl -k -s -u root:0penBmc -X POST \
  https://<BMC_IP>/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}'

# Force Off (long press 4s)
curl -k -s -u root:0penBmc -X POST \
  https://<BMC_IP>/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceOff"}'

# Graceful Shutdown (short press, OS handles ACPI event)
curl -k -s -u root:0penBmc -X POST \
  https://<BMC_IP>/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "GracefulShutdown"}'

# Force Restart (Reset pulse 500ms)
curl -k -s -u root:0penBmc -X POST \
  https://<BMC_IP>/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceRestart"}'

# Query Host Power State
curl -k -s -u root:0penBmc \
  https://<BMC_IP>/redfish/v1/Systems/system | jq '.PowerState'
```

### D-Bus Commands (SSH into BMC)

```bash
# Query Host Power State
busctl get-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host CurrentHostState

# Query Chassis Power State
busctl get-property xyz.openbmc_project.State.Chassis \
  /xyz/openbmc_project/state/chassis0 \
  xyz.openbmc_project.State.Chassis CurrentPowerState

# Request Power On
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.On"

# Request Power Off
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.Off"

# Request Reboot
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.Reboot"
```

### gpiolib Commands (SSH into BMC)

```bash
# List all gpiochips (MA35 has one per port)
gpiodetect

# Find lines by name (recommended)
gpioinfo | grep -E "POWER_OUT|RESET_OUT|PS_PWROK"

# Find specific line
gpiofind POWER_OUT
gpiofind RESET_OUT
gpiofind PS_PWROK

# Read PS_PWROK state: 1=Host on, 0=Host off
gpioget $(gpiofind PS_PWROK)

# Manual power button press (200ms low pulse)
gpioset -m time -u 200000 $(gpiofind POWER_OUT)=0

# Manual force off (4s low pulse)
gpioset -m time -u 4000000 $(gpiofind POWER_OUT)=0

# Manual reset pulse (500ms)
gpioset -m time -u 500000 $(gpiofind RESET_OUT)=0
```

## Oscilloscope Verification

### Probe Connections

```
- CH1: PN1 (POWER_OUT)
- CH2: PN0 (RESET_OUT)
- CH3: PK12 (PS_PWROK)
- GND: BMC board GND
- Trigger: Falling edge, CH1 or CH2
- Timebase: 1s/div
```

### Quick Reference Table

| Operation | API | Observe Pin | Pulse Polarity | Expected Width |
|-----------|-----|-------------|----------------|----------------|
| Power On | Redfish `On` / D-Bus `Transition.On` | **PN1** (CH1) | Active LOW | 200ms |
| Graceful Shutdown | Redfish `GracefulShutdown` / D-Bus `Transition.Off` | **PN1** (CH1) | Active LOW | 200ms (first) |
| Force Off | Redfish `ForceOff` | **PN1** (CH1) | Active LOW | 4000ms |
| Force Restart | Redfish `ForceRestart` / D-Bus `Transition.Reboot` | **PN0** (CH2) | Active LOW | 500ms |
| Power Detection | Query Chassis PowerState | **PK12** (CH3) | Read DC level | HIGH=On, LOW=Off |

## Notes

- `x86-power-control` uses `libgpiod` with line names — no hard-coded GPIO numbers needed
- POWER_OUT/RESET_OUT idle state is HIGH (3.3V), pulled to LOW (0V) when triggered
- PS_PWROK is continuously monitored; if floating, add 10kΩ pull-down to ensure LOW when off
- D-Bus `Transition.Off` = graceful-first-then-force (200ms → wait 300s → 4000ms)
- Redfish `ForceOff` = immediate 4s pulse
