# MA35D16FJ87C OpenBMC Functions Integration Test Report

**Platform**: NuMaker-IoT-MA35D16FJ87C  
**BMC Hostname**: numaker-iot-ma35d16fj87c.local  

---

## Test Results

- **GET Service Root**: ✓ HTTP 200
- **GET Chassis Collection**: ✓ HTTP 200
- **GET Chassis Details (system)**: ✓ HTTP 200
- **GET System Details**: ✓ HTTP 200
- **PATCH Set LocationIndicatorActive=true**: ✓ HTTP 204
- **GET Verify LocationIndicatorActive State**: ✓ HTTP 200
- **PATCH Set LocationIndicatorActive=false**: ✓ HTTP 204
- **GET BMC Manager Status**: ✓ HTTP 200
- **GET System/Host Status (PowerState, Health)**: ✓ HTTP 200
- **GET Chassis ThermalSubsystem**: ✓ HTTP 200
- **GET Chassis PowerSubsystem**: ✓ HTTP 200
- **GET Chassis Sensor Collection**: ✓ HTTP 200
- **GET BMC Log Services Collection**: ✓ HTTP 200
- **GET BMC Journal Entries**: ✓ HTTP 200
- **GET System Log Services Collection**: ✓ HTTP 200
- **GET System EventLog Entries**: ✓ HTTP 200
- **GET Event Service Status**: ✓ HTTP 200

### User Management (AccountService)

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

### Host Power Controls (GPIO)

- **GET Chassis Power State (Initial)**: ✓ HTTP 200
- **POST Host Power On (PK12=HIGH)**: ✓ HTTP 204 (PowerState=On)
- **POST Host ForceOff (PK12=LOW)**: ✓ HTTP 204 (PowerState=Off)
- **POST Host ForceRestart (PK12=HIGH)**: ✓ HTTP 204 (PowerState=On)

### Firmware Update via Redfish (Dual-Bank OTA & Anti-Rollback)

- **GET UpdateService Root (`/redfish/v1/UpdateService`)**: ✓ HTTP 200 (ServiceEnabled=true, HttpPushUri supported)
- **GET Firmware Inventory Collection**: ✓ HTTP 200 (Active BMC, Bootloader, and Kernel enumerated)
- **POST Mismatched Machine Model Rejection**: ✓ HTTP 400 (Candidate targeting incompatible model blocked)
- **POST Anti-Rollback Version Downgrade Rejection**: ✓ HTTP 400 (`FirmwareRollbackProhibited` enforced)
- **POST Identical Version Re-Flash Acceptance**: ✓ HTTP 202 (Permitted for repair re-flashing)
- **POST Upload Valid OTA Tarball (Multipart/Stream)**: ✓ HTTP 202 (Task URI returned)
- **GET Task Progress Tracking**: ✓ HTTP 200 (TaskState transitioned: Starting -> Running -> Completed 100%)
- **Dual-Bank Inactive Flashing Verification**: ✓ PASS (Alternate bank written while BMC online)
- **U-Boot Autonomous Rollback Verification**: ✓ PASS (`bootcount > bootlimit` triggers automatic reversal)
- **Post-Boot Service Health Confirmation**: ✓ PASS (`obmc-boot-verify.service` resets bootcount to 0)
- **Persistent Configuration Retention**: ✓ PASS (`/var/persist` accounts and network preserved)
