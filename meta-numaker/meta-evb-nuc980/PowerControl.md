# NUC980 GPIO Power Control

## Overview

NuMaker-IoT-NUC980G2 serves as a BMC, controlling the Host power via GPIO.
It uses OpenBMC's `x86-power-control` daemon with `libgpiod` to operate GPIO lines.

## Hardware Signal Definitions

| Signal Name | Direction | Function | Suggested Pin | GPIO# (hex) | GPIO# (dec) |
|-------------|-----------|----------|---------------|-------------|-------------|
| `POWER_OUT` | Output | Emulates ATX power button (200ms=power on, 4s=force off) | PD12 | 0x6C | 108 |
| `RESET_OUT` | Output | Emulates reset button (pull low for 200ms) | PD13 | 0x6D | 109 |
| `PS_PWROK` | Input | Detects Host PSU Power Good | | 0xA9 | 169 |

## Wiring Diagram

```
NUC980 (BMC)                   Host Motherboard
────────────                   ────────────────
PD12 (POWER_OUT)  ─────────── PWR_BTN# (power button header)
PD13 (RESET_OUT)  ─────────── RST_BTN# (reset button header)
PF9  (PS_PWROK)   ◄────────── PWROK (ATX PSU / VRM output)
GND ──────────────────────── GND (common ground)
```

> **Electrical Specs**: NUC980 GPIO is 3.3V. POWER_OUT/RESET_OUT are open-drain (active low, Host side has pull-up resistors).

## Commands

### Redfish API

```bash
# Power On (short press 200ms)
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}'

# Force Off (long press 4s)
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceOff"}'

# Graceful Shutdown (short press, OS handles ACPI event)
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "GracefulShutdown"}'

# Force Restart (Reset pulse 500ms)
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "ForceRestart"}'

# Query Host Power State
curl -k -s -u root:0penBmc \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system | jq '.PowerState'

# Query Supported ResetTypes
curl -k -s -u root:0penBmc \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system | jq '.Actions."#ComputerSystem.Reset"'
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

# Request Chassis Power Off
busctl set-property xyz.openbmc_project.State.Chassis \
  /xyz/openbmc_project/state/chassis0 \
  xyz.openbmc_project.State.Chassis RequestedPowerTransition \
  s "xyz.openbmc_project.State.Chassis.Transition.Off"

# List all D-Bus objects for power-control
busctl tree xyz.openbmc_project.State.Host

# Check power-control daemon status
systemctl status xyz.openbmc_project.Chassis.Control.Power@0.service
journalctl -u xyz.openbmc_project.Chassis.Control.Power@0.service --no-pager -n 20
```

### gpiolib Commands (SSH into BMC)

```bash
# --- Query GPIO Info ---

# List all gpiochips
gpiodetect

# List all GPIO lines (with names and usage status)
gpioinfo gpiochip0

# Filter named power control lines
gpioinfo gpiochip0 | grep -E "POWER_OUT|RESET_OUT|PS_PWROK|POST_COMPLETE"

# Find line number by name
gpiofind PS_PWROK

# --- Read Input ---

# Read PS_PWROK (PF9, line 169): 1=Host on, 0=Host off <Device or resource busy>
gpioget gpiochip0 169

# Read by name
gpioget $(gpiofind PS_PWROK)

# Read POST_COMPLETE (PF10, line 170)
gpioget gpiochip0 170

# --- Manual Output Control ---

# Emulate short power button press (power on, 200ms low pulse)
gpioset gpiochip0 108=0 && sleep 0.2 && gpioset gpiochip0 108=1

# Emulate long power button press (force off, 4s low pulse)
gpioset gpiochip0 108=0 && sleep 4 && gpioset gpiochip0 108=1

# Emulate Reset (500ms low pulse)
gpioset gpiochip0 109=0 && sleep 0.5 && gpioset gpiochip0 109=1

# --- Real-time GPIO Event Monitoring ---

# Monitor PS_PWROK rising/falling edges (power on/off events) <Device or resource busy>
gpiomon --rising-edge --falling-edge gpiochip0 169

# Monitor POST_COMPLETE
gpiomon --rising-edge gpiochip0 170
```

## Oscilloscope Verification Steps

### Preparation

```
Oscilloscope probe connections:
- CH1: PD12 (POWER_OUT) — corresponding pin on J6 header
- CH2: PD13 (RESET_OUT) — corresponding pin on J6 header
- CH3: PF9  (PS_PWROK)  — corresponding pin on J6 header (observe feedback)
- GND: BMC board GND
- Trigger: Falling edge, CH1 or CH2
- Timebase: 1s/div (to cover 4s ForceOff pulse)
```

### Step 1: Power On — Measure PD12

```bash
# Redfish
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" -d '{"ResetType": "On"}'

# Or D-Bus (SSH into BMC)
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.On"
```

| Channel | Expected Waveform |
|---------|-------------------|
| **CH1 (PD12)** | HIGH → LOW → HIGH, low pulse width **≈200ms** |
| CH2 (PD13) | No change, stays HIGH |
| CH3 (PF9) | If Host boots normally, goes LOW → HIGH after several hundred ms |

### Step 2: Confirm Power On Success — Observe PF9

```bash
# Redfish
curl -k -s -u root:0penBmc \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system | jq '.PowerState'
# Expected: "On"

# D-Bus (SSH into BMC)
busctl get-property xyz.openbmc_project.State.Chassis \
  /xyz/openbmc_project/state/chassis0 \
  xyz.openbmc_project.State.Chassis CurrentPowerState
# Expected: s "xyz.openbmc_project.State.Chassis.PowerState.On"
```

| Channel | Expected |
|---------|----------|
| CH3 (PF9) | Stable HIGH (3.3V) — Host PSU power OK |

### Step 3: Graceful Shutdown — Measure PD12 (Graceful First, Then Force)

```bash
# D-Bus (sends 200ms graceful first, waits 300s, then ForceOff)
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.Off"

# Or Redfish GracefulShutdown
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" -d '{"ResetType": "GracefulShutdown"}'
```

| Channel | Expected Waveform |
|---------|-------------------|
| **CH1 (PD12)** | First: low pulse **≈200ms** (notifies OS ACPI shutdown) |
| CH3 (PF9) | If OS shuts down normally: HIGH → LOW after several seconds |
| **CH1 (PD12)** | If 300s timeout and PF9 still HIGH: second low pulse **≈4000ms** (ForceOff) |

> **Note**: D-Bus `Transition.Off` behavior is "graceful first, then force" — 200ms graceful first, 4000ms force if timeout.

### Step 4: Force Off — Measure PD12 (Immediate 4s)

```bash
# Redfish ForceOff (sends 4000ms directly, no graceful wait)
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" -d '{"ResetType": "ForceOff"}'
```

| Channel | Expected Waveform |
|---------|-------------------|
| **CH1 (PD12)** | HIGH → LOW → HIGH, low pulse width **≈4000ms (4s)** |
| CH2 (PD13) | No change |
| CH3 (PF9) | HIGH → LOW (Host powers off) several seconds after pulse ends |

### Step 5: Force Restart — Measure PD13

```bash
# Redfish ForceRestart
curl -k -s -u root:0penBmc -X POST \
  https://numaker-iot-nuc980g2.local/redfish/v1/Systems/system/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" -d '{"ResetType": "ForceRestart"}'

# Or D-Bus Reboot
busctl set-property xyz.openbmc_project.State.Host \
  /xyz/openbmc_project/state/host0 \
  xyz.openbmc_project.State.Host RequestedHostTransition \
  s "xyz.openbmc_project.State.Host.Transition.Reboot"
```

| Channel | Expected Waveform |
|---------|-------------------|
| CH1 (PD12) | No change (or ForceOff+On combo, depending on daemon implementation) |
| **CH2 (PD13)** | HIGH → LOW → HIGH, low pulse width **≈500ms** |
| CH3 (PF9) | Brief LOW then back to HIGH (Host powers back up) |

### Step 6: Chassis Off — Measure PD12 + PF9

```bash
# D-Bus Chassis Off
busctl set-property xyz.openbmc_project.State.Chassis \
  /xyz/openbmc_project/state/chassis0 \
  xyz.openbmc_project.State.Chassis RequestedPowerTransition \
  s "xyz.openbmc_project.State.Chassis.Transition.Off"
```

| Channel | Expected Waveform |
|---------|-------------------|
| **CH1 (PD12)** | Low pulse **≈4000ms** (ForceOff) |
| CH3 (PF9) | HIGH → LOW (confirms Host completely powered off) |

### Quick Reference Table

| Operation | API | Observe Pin | Pulse Polarity | Expected Width |
|-----------|-----|-------------|----------------|----------------|
| Power On | Redfish `On` / D-Bus `Transition.On` | **PD12** (CH1) | Active LOW | 200ms |
| Graceful Shutdown | Redfish `GracefulShutdown` / D-Bus `Transition.Off` | **PD12** (CH1) | Active LOW | 200ms (first) |
| Force Off | Redfish `ForceOff` | **PD12** (CH1) | Active LOW | 4000ms |
| Force Restart | Redfish `ForceRestart` / D-Bus `Transition.Reboot` | **PD13** (CH2) | Active LOW | 500ms |
| Power Detection | Query Chassis PowerState | **PF9** (CH3) | Read DC level | HIGH=On, LOW=Off |

### Notes

- When PD12/PD13 are occupied by daemon, they are outputs; idle state is HIGH (3.3V), pulled to LOW (0V) when triggered
- PF9 is input, continuously monitored by daemon; gpioget/gpiomon will fail with `Device or resource busy`
- If PF9 is floating (not connected), readings may be unstable (add 10kΩ pull-down)
- D-Bus `Transition.Off` ≠ Redfish `ForceOff`: former is graceful-first-then-force (200ms → wait 300s → 4000ms), latter is immediate 4s

## Current Status

- `x86-power-control` daemon operates POWER_OUT (PD12) and RESET_OUT (PD13) via libgpiod
- PowerOk monitors PS_PWROK (PF9) to detect Host power state
- Redfish / D-Bus Power Control API working properly
- PF9 should be connected to motherboard PWR_LED+ or ATX PWROK, with 10kΩ pull-down to ensure LOW when powered off
