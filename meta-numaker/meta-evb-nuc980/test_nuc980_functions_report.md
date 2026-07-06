# NUC980 OpenBMC Functions Integration Test Report

**Date**: 2026-07-06 18:58:25
**BMC IP**: numaker-iot-nuc980g2.local
**Platform**: NuMaker-IoT-NUC980G2

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

- **Power On**: 已提示操作者在 PF9 接上 HIGH 信號
- **POST Host Power On**: ✓ HTTP 204
- **GET Verify Host PowerState after Power On**: ✓ HTTP 200
- **Verify Power On**: PowerState=On
- **Force Off**: 已提示操作者準備讓 PF9 回到 LOW
- **POST Host ForceOff**: ✓ HTTP 204
- **GET Verify Host PowerState after ForceOff**: ✓ HTTP 200
- **Verify Force Off**: PowerState=Off
- **Force Restart**: 已確認 PF9=HIGH
- **POST Host ForceRestart**: ✓ HTTP 204
- **GET Verify Host PowerState after ForceRestart**: ✓ HTTP 200
- **Verify Force Restart**: PowerState=On

---

## Summary

- Test completed at: 2026-07-06 19:00:01
- Report file: ./test_nuc980_functions_report.md
