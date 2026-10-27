# NUC980 OpenBMC Functions Integration Test Report

**Platform**: NuMaker-IoT-NUC980G2  
**BMC Hostname**: numaker-iot-nuc980g2.local  

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

### Host Power Controls (GPIO)

- **GET Chassis Power State (Initial)**: ✓ HTTP 200
- **POST Host Power On (PF9=HIGH)**: ✓ HTTP 204 (PowerState=On)
- **POST Host ForceOff (PF9=LOW)**: ✓ HTTP 204 (PowerState=Off)
- **POST Host ForceRestart (PF9=HIGH)**: ✓ HTTP 204 (PowerState=On)
