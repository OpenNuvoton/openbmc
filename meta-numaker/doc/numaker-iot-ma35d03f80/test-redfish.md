# MA35D03F80 OpenBMC Functions Integration Test Report

**Date**: 2026-10-08 15:52:55
**BMC IP**: numaker-iot-ma35d03f80.local
**Platform**: NuMaker-IoT-MA35D03F80

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

### User Management

- **GET AccountService Root**: ✓ HTTP 200
- **GET Accounts Collection**: ✓ HTTP 200
- **POST Create Test Account (rftestuser)**: ✓ HTTP 201
- **GET Verify New Account (rftestuser)**: ✓ HTTP 200
- **Login as rftestuser**: ✓ HTTP 200
- **PATCH Change Role to ReadOnly**: ✓ HTTP 204
- **PATCH Disable Account**: ✓ HTTP 204
- **Verify Disabled Account Rejected**: ✓ HTTP 401
- **DELETE Delete Test Account (rftestuser)**: ✓ HTTP 200
- **Verify Account Removed**: ✓ HTTP 404
- **LDAP Functionally Configured**: false (expected: false)

### Power Controls

- **GET Chassis Power State (before action)**: ✓ HTTP 200

### Power Control Tests

