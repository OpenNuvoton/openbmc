# MA35D05K OpenBMC Functions Integration Test Report

**Date**: 2026-07-07 17:49:01
**BMC IP**: numaker-iot-ma35d05ki1.local
**Platform**: NuMaker-IoT-MA35D05KI1

---

## Test Results

- **GET Service Root**: ✓ HTTP 200
- **GET Chassis Collection**: ✓ HTTP 200
- **GET Chassis Details (system)**: ✓ HTTP 200
- **GET System details**: ✓ HTTP 200
- **PATCH Set LocationIndicatorActive=true**: ✓ HTTP 204
- **GET Verify LocationIndicatorActive state**: ✓ HTTP 200
- **PATCH Set LocationIndicatorActive=false**: ✓ HTTP 204
- **GET BMC Manager Status**: ✓ HTTP 200
- **GET System/Host Status (PowerState, Health)**: ✓ HTTP 200
- **GET Chassis ThermalSubsystem**: ✓ HTTP 200
- **GET Chassis PowerSubsystem**: ✓ HTTP 200
- **GET Chassis Sensor Collection**: ✓ HTTP 200
- **GET BMC Log Services Collection**: ✓ HTTP 200
- **GET BMC Journal Entries (latest 5)**: ✓ HTTP 200
- **GET System Log Services Collection**: ✓ HTTP 200
- **GET System EventLog Entries (latest 5)**: ✓ HTTP 200
- **GET Event Service Status**: ✓ HTTP 200

### Power Controls

- **GET Chassis Power State (before action)**: ✓ HTTP 200

### Power Control Tests

- **Power On**: Operator prompted to connect PC7 to HIGH
- **POST Host Power On**: ✓ HTTP 204
- **GET Verify Host PowerState after Power On**: ✓ HTTP 200
- **Verify Power On**: PowerState=On
- **Force Off**: Operator prompted to disconnect PC7 to LOW
- **POST Host ForceOff**: ✓ HTTP 204
- **GET Verify Host PowerState after ForceOff**: ✓ HTTP 200
- **Verify Force Off**: PowerState=Off
- **Force Restart**: Confirmed PC7=HIGH
- **POST Host ForceRestart**: ✓ HTTP 204
- **GET Verify Host PowerState after ForceRestart**: ✓ HTTP 200
- **Verify Force Restart**: PowerState=On

---

## Summary

- Test completed at: 2026-07-07 17:50:06
- Report file: ./numaker-iot-ma35d05ki1.md
