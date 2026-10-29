# NuMaker-IoT-MA35D03F80 Redfish Firmware Update (OTA) Guide

Operational guide for over-the-air (OTA) firmware updates on the **NuMaker-IoT-MA35D03F80** using the DMTF Redfish `UpdateService` API, covering dual-bank (A/B) storage layouts, direct-to-disk streaming, anti-rollback checks, watchdog boot fallback, and automated test scripts.

---

## Table of Contents

1. [Architecture & Update Mechanism](#1-architecture--update-mechanism)
   - [1.1 SPI-NAND / Raw NAND: Pure UBI Dual-Bank Layout](#11-spi-nand--raw-nand-pure-ubi-dual-bank-layout)
   - [1.2 SD1 / eMMC: MBR EXT4 Dual-Bank Layout](#12-sd1--emmc-mbr-ext4-dual-bank-layout)
   - [1.3 Direct-to-Disk Streaming (Low-Memory OOM Prevention)](#13-direct-to-disk-streaming-low-memory-oom-prevention)
   - [1.4 Target Verification & Anti-Rollback](#14-target-verification--anti-rollback)
   - [1.5 Watchdog Boot Fallback](#15-watchdog-boot-fallback)
2. [Prerequisites](#2-prerequisites)
   - [2.1 Host PC Dependencies](#21-host-pc-dependencies)
   - [2.2 Default BMC Connection Info](#22-default-bmc-connection-info)
   - [2.3 Firmware Update Tarball Format](#23-firmware-update-tarball-format)
3. [Automated Test Scripts](#3-automated-test-scripts)
   - [3.1 End-to-End Firmware Update (`test-redfish-update.sh`)](#31-end-to-end-firmware-update-test-redfish-updatesh)
   - [3.2 Anti-Rollback & Machine Check (`test-rollback-guard.sh`)](#32-anti-rollback--machine-check-test-rollback-guardsh)
   - [3.3 Watchdog Boot Fallback (`test-boot-fallback.sh`)](#33-watchdog-boot-fallback-test-boot-fallbacksh)
4. [Manual Redfish Update via `curl`](#4-manual-redfish-update-via-curl)
   - [Step 1: Query Current Firmware Inventory](#step-1-query-current-firmware-inventory)
   - [Step 2: Upload Firmware Package](#step-2-upload-firmware-package)
   - [Step 3: Monitor Task Progress](#step-3-monitor-task-progress)
   - [Step 4: Verify Reboot & Active Bank](#step-4-verify-reboot--active-bank)
5. [Diagnostics & Troubleshooting](#5-diagnostics--troubleshooting)

---

## 1. Architecture & Update Mechanism

### 1.1 SPI-NAND / Raw NAND: Pure UBI Dual-Bank Layout

SPI-NAND (512 MB) and Raw NAND (1024 MB) use a two-partition MTD layout, delegating wear-leveling and bad-block management to UBI:

```text
SPI-NAND (512MB) / Raw NAND (1024MB) UBI Layout
+-------------------------+-----------------------------------------------------------+
| mtd0: uboot             | mtd1: rootfs (Pure UBI Pool)                              |
| 0x00000000 - 0x00400000 | 0x00400000 - 0x20000000 (508 MB on 512MB SPI-NAND)        |
| (4 MB Raw Bootloader)   | 0x00400000 - 0x40000000 (1020 MB on 1GB Raw NAND)         |
|                         |                                                           |
|  * Header               |  |-- Vol 0: u-boot-env (256 KB, preloaded 64KB env)       |
|  * BL2 DTB              |  |-- Vol 1: kernel-a   (16 MB, Bank A Kernel)             |
|  * BL2 Bin              |  |-- Vol 2: dtb-a      (512 KB, Bank A DTB)               |
|  * FIP (BL31 + U-Boot)  |  |-- Vol 3: rofs-a     (100 MB, Bank A UBIFS RootFS)      |
|                         |  |-- Vol 4: kernel-b   (16 MB, Bank B Kernel Standby)     |
|                         |  |-- Vol 5: dtb-b      (512 KB, Bank B DTB Standby)       |
|                         |  |-- Vol 6: rofs-b     (100 MB, Bank B UBIFS Standby)     |
|                         |  `-- Vol 7: rwfs       (10 MB autoresize -> ~255MB/~760MB)|
+-------------------------+-----------------------------------------------------------+
```

| MTD Partition | Label | Size & Offset | Contents & UBI Volumes |
| :--- | :--- | :--- | :--- |
| **`mtd0`** | `spinand-uboot`<br>`nand-uboot` | 4 MB<br>(`0x0`–`0x400000`) | **Raw Bootloader**: Header + BL2 DTB + BL2 Bin + FIP (BL31 + U-Boot) |
| **`mtd1`** | `spinand-rootfs`<br>`nand-rootfs` | 508 MB (SPI-NAND)<br>1020 MB (Raw NAND) | **Pure UBI Pool**:<br>• `Vol 0 (u-boot-env)`: 256 KB, U-Boot environment<br>• `Vol 1 (kernel-a)`: 16 MB, Bank A Linux kernel<br>• `Vol 2 (dtb-a)`: 512 KB, Bank A device tree<br>• `Vol 3 (rofs-a)`: 100 MB, Bank A UBIFS read-only rootfs<br>• `Vol 4 (kernel-b)`: 16 MB, Bank B standby kernel<br>• `Vol 5 (dtb-b)`: 512 KB, Bank B standby device tree<br>• `Vol 6 (rofs-b)`: 100 MB, Bank B standby UBIFS rootfs<br>• `Vol 7 (rwfs)`: 10 MB (autoresizes to fill remaining flash, mounted at `/var/persist`) |

- **Dual-Bank Update Flow**:
  - The updater inspects `/proc/cmdline` and `/proc/mounts` to identify the active bank.
  - When running on Bank A, `ubiupdatevol` writes the incoming image to Bank B (`kernel-b`, `dtb-b`, `rofs-b`), and vice versa when running on Bank B.
  - Once all volumes are written, `fw_setenv` updates the U-Boot boot pointers (`bootubivol`, `kernelname`, `dtbname`).
- **Bootloader Write Guard**:
  - Before erasing and writing `image-u-boot` (4 MB) to `mtd0`, the updater compares its SHA-256 digest against the existing `mtd0` contents and skips flashing if identical, reducing flash wear and power-loss exposure.

---

### 1.2 SD1 / eMMC: MBR EXT4 Dual-Bank Layout

SD cards and eMMC manage wear-leveling internally via their hardware FTL and use standard **EXT4** partitions.

> [!NOTE]
> **Why MBR (`msdos`) Instead of GPT?**
> The MA35 internal boot ROM (IBR) reads the boot header from **Sector 2 (`0x400`)** on SD/eMMC devices. A GPT partition table places its primary header and partition entries across LBA 1–33 (`0x200`–`0x43FF`), colliding with Sector 2. SD1 and eMMC therefore use a standard **MBR (`msdos`)** partition table.

```text
SD1 (MicroSD) / eMMC MBR Dual-Bank Layout
+------------------------+---------+---------+----------+----------+---------------------------------+
| Sector 0 ~ 8191        | Part 1  | Part 2  | Part 3   | Part 4   | Logical Partitions              |
| 0x00000000-0x00400000  | boot-a  | boot-b  | rofs-a   | Extended | Part 5       | Part 6           |
| 4MB Raw Bootloader/UBL | (32 MB) | (32 MB) | (256 MB) | Container| rofs-b       | rwfs             |
|  * MBR (Sector 0)      | Bank A  | Bank B  | Bank A   | (1 sec)  | (256 MB)     | (256 MB ~ 15GB+) |
|  * Header (Sector 2)   | Kernel  | Kernel  | RootFS   |          | Bank B       | /images (staging)|
|  * BL2 DTB (0x20000)   | (EXT4)  | (EXT4)  | (EXT4)   |          | RootFS       | /var/persist     |
|  * BL2 Bin (0x30000)   |         |         |          |          | (EXT4)       | (EXT4)           |
|  * FIP (0xC0000)       |         |         |          |          |              |                  |
|  * U-Boot Env (0x50000)|         |         |          |          |              |                  |
+------------------------+---------+---------+----------+----------+---------------------------------+
```

| Device Node (SD1 example) | Label | Default Size | Filesystem | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`/dev/mmcblk1` (first 4 MB)** | (Raw Sectors) | 4 MB | Raw Binary | **Bootloader**: MBR, IBR Header (`0x400`), BL2 DTB, BL2 Bin, FIP, and U-Boot Env (`0x50000`) |
| **`/dev/mmcblk1p1`** | `boot-a` | 32 MB | EXT4 | **Bank A Boot**: Linux kernel (`Image`) + DTB (`Image.dtb`) |
| **`/dev/mmcblk1p2`** | `boot-b` | 32 MB | EXT4 | **Bank B Boot**: Standby kernel + DTB |
| **`/dev/mmcblk1p3`** | `rofs-a` | 256 MB | EXT4 | **Bank A RootFS**: Read-only rootfs (`/`) |
| **`/dev/mmcblk1p4`** | (Extended) | 1 sector | Extended | **MBR Extended Partition**: Container for logical partitions `p5` and `p6` |
| **`/dev/mmcblk1p5`** | `rofs-b` | 256 MB | EXT4 | **Bank B RootFS**: Standby read-only rootfs |
| **`/dev/mmcblk1p6`** | `rwfs` | 256 MB+ (resizable) | EXT4 | **Persistent Overlay & OTA Staging**: Mounted at `/var/persist` and `/images` |

- **Dual-Bank Update Flow**:
  - Upload `obmc-phosphor-image-numaker-iot-ma35d03f80.mmc-ext4-tar`.
  - **Active Bank A** (`bootside=a`, `root=/dev/mmcblk1p3`): Kernel is written to `p2` (`boot-b`) and RootFS to `p5` (`rofs-b`).
  - **Active Bank B** (`bootside=b`, `root=/dev/mmcblk1p5`): Kernel is written to `p1` (`boot-a`) and RootFS to `p3` (`rofs-a`).
  - **Post-Flash Sync**: After writing the standby rootfs, the updater copies `bind-images.sh`, `obmc-flash-bmc`, `obmc-boot-verify.service`, and `/etc/fw_env.config` into the target partition.
  - **Boot Pointer Switch**: Updates U-Boot environment variables (`bootside=b` or `a`, `bootcount=0`, `upgrade_available=1`).

#### Online Partition Resize on SD Cards
The initial WIC image allocates 256 MB to partition 6 (`rwfs`). Because `p6` is mounted online (`/images` and `/var/persist`), `parted -s` (`--script`) aborts on the busy-partition warning; pass `echo yes | parted ---pretend-input-tty` (three leading hyphens) to confirm online expansion before staging large (`170 MB+`) EXT4 OTA packages:
```bash
echo yes | parted ---pretend-input-tty /dev/mmcblk1 resizepart 4 100%
echo yes | parted ---pretend-input-tty /dev/mmcblk1 resizepart 6 100%
resize2fs /dev/mmcblk1p6
df -h /var/persist
```

---

### 1.3 Direct-to-Disk Streaming (Low-Memory OOM Prevention)

- Available system RAM on MA35 boards is ~125–500 MB, whereas full OTA tarballs range from 55 MB to 170 MB.
- Upstream `bmcweb` buffers entire HTTP request payloads in heap memory, which triggers the Linux OOM killer on large uploads.
- The `bmcweb` direct-to-disk streaming patch:
  1. Streams HTTP payloads exceeding 10 MB directly to `/tmp/images` on disk.
  2. Keeps `bmcweb` RSS memory overhead under 5 MB during upload.
  3. Calls `malloc_trim(0)` immediately after transfer completion to return heap pages to the kernel.

---

### 1.4 Target Verification & Anti-Rollback

Before extracting or writing flash partitions, [`ma35-verify-version.sh`](file:///usr/bin/ma35-verify-version.sh) validates the incoming `MANIFEST`:
1. **Machine Check (`MachineName`)**: Verifies `MachineName=numaker-iot-ma35d03f80`. Mismatched packages are rejected (`HTTP 400` / `TaskAborted`).
2. **Anti-Rollback (`SecurityVersion`)**: Compares the package `SecurityVersion` against the running system baseline and aborts if the incoming version is lower.

---

### 1.5 Watchdog Boot Fallback

- After an OTA update switches to the standby bank, U-Boot sets `bootcount=0`, `bootlimit=3`, and `upgrade_available=1`.
- U-Boot increments `bootcount` on every boot while `upgrade_available=1`:
  - **Normal Boot**: Once userspace reaches multi-user state, [`obmc-boot-verify.service`](file:///lib/systemd/system/obmc-boot-verify.service) clears `bootcount=0` and `upgrade_available=0` to commit the new bank.
  - **Boot Failure**: If the new kernel or rootfs panics or hangs and the hardware watchdog resets the board beyond `bootlimit` (3 attempts), U-Boot's `altbootcmd` automatically reverts the boot pointers back to the previous working bank.

---

## 2. Prerequisites

### 2.1 Host PC Dependencies

Install the required CLI utilities on your Linux workstation:
```bash
sudo apt-get update
sudo apt-get install -y curl sshpass jq tar
```

### 2.2 Default BMC Connection Info

| Parameter | Default Value | Notes |
| :--- | :--- | :--- |
| **BMC Hostname** | `numaker-iot-ma35d03f80.local` | Resolved via mDNS (`avahi-daemon`) |
| **Redfish Username** | `root` | `Administrator` role |
| **Redfish Password** | `0penBmc` | Default password (zero `0`) |
| **Redfish Port** | `443` | HTTPS with self-signed certificate (use `curl -k`) |

Verify connectivity from the host PC:
```bash
ping -c 2 numaker-iot-ma35d03f80.local
```

### 2.3 Firmware Update Tarball Format

#### 1. SPI-NAND / Raw NAND Package (`*.mtd-ubi-tar`)
```text
obmc-phosphor-image-numaker-iot-ma35d03f80.mtd-ubi-tar
├── MANIFEST            # Metadata (version, MachineName, SecurityVersion)
├── image-kernel        # Linux kernel Image (written to kernel-a / kernel-b)
├── image-dtb           # Device tree blob (written to dtb-a / dtb-b)
├── image-rofs          # UBIFS rootfs image (written to rofs-a / rofs-b)
├── image-u-boot        # (Optional) 4 MB SPI-NAND bootloader image
├── image-u-boot-nand   # (Optional) 4 MB Raw NAND bootloader image
└── image-rwfs          # Placeholder file required by phosphor-software-manager
```

#### 2. SD1 / eMMC Package (`*.mmc-ext4-tar`)
```text
obmc-phosphor-image-numaker-iot-ma35d03f80.mmc-ext4-tar
├── MANIFEST            # Metadata (version, MachineName, SecurityVersion)
├── image-kernel        # Linux kernel Image (written to boot-a / boot-b)
├── image-rofs          # EXT4 rootfs image (written to rofs-a / rofs-b)
├── image-u-boot        # 4 MB bootloader image (Header + BL2 + FIP)
└── image-rwfs          # Placeholder file required by phosphor-software-manager
```

Example `MANIFEST`:
```ini
purpose=xyz.openbmc_project.Software.Version.VersionPurpose.BMC
version=2.15.0-ma35d03f80
MachineName=numaker-iot-ma35d03f80
SecurityVersion=4
ExtendedVersion=openbmc-build-20261021
```

---

## 3. Automated Test Scripts

All test scripts are located in `meta-numaker/doc/numaker-iot-ma35d03f80/test-redfish-update/`.

> [!NOTE]
> Run these scripts from your **Host Linux PC** over the network—do not run them inside the BMC shell.

### 3.1 End-to-End Firmware Update (`test-redfish-update.sh`)

Uploads the firmware tarball, polls the Redfish task monitor until completion, waits for the BMC to reboot, and verifies that the active bank switched.

Usage:
```bash
./test-redfish-update.sh <BMC_IP> <IMAGE_FILE> [username:password] [Immediate|OnReset]
```

Example (SPI-NAND / Raw NAND):
```bash
bash meta-numaker/doc/numaker-iot-ma35d03f80/test-redfish-update/test-redfish-update.sh \
  numaker-iot-ma35d03f80.local \
  build-ma35/tmp/deploy/images/numaker-iot-ma35d03f80/obmc-phosphor-image-numaker-iot-ma35d03f80.mtd-ubi-tar \
  root:0penBmc \
  Immediate
```

Example (SD1 / eMMC):
```bash
bash meta-numaker/doc/numaker-iot-ma35d03f80/test-redfish-update/test-redfish-update.sh \
  numaker-iot-ma35d03f80.local \
  build-ma35/tmp/deploy/images/numaker-iot-ma35d03f80/obmc-phosphor-image-numaker-iot-ma35d03f80.mmc-ext4-tar \
  root:0penBmc \
  Immediate
```

**Execution Flow**:
1. **[STEP 1] Upload Firmware**: Checks Redfish `UpdateService` readiness, posts the tarball, and captures the `202 Accepted` task monitor URI.
2. **[STEP 2] Monitor Progress**: Polls the task monitor (`0%` → `100%`) until flashing completes and the BMC reboots.
3. **[STEP 3] Wait for Reboot**: Polls the BMC until Redfish comes back online (~30–50 seconds).
4. **[STEP 4] Verify Inventory**: Queries `/redfish/v1/UpdateService/FirmwareInventory` to confirm the updated version.
5. **[STEP 5] Verify Active Bank**: Connects via SSH to verify U-Boot environment variables and `/proc/cmdline`.

---

### 3.2 Anti-Rollback & Machine Check (`test-rollback-guard.sh`)

Verifies that packages with a mismatched `MachineName` or downgraded `SecurityVersion` are rejected.

```bash
./test-rollback-guard.sh numaker-iot-ma35d03f80.local root:0penBmc
```

**Test Cases**:
1. **Inventory Check**: Verifies `/redfish/v1/UpdateService/FirmwareInventory` responds.
2. **Machine Mismatch Rejection**: Generates and uploads a synthetic tarball with `MachineName=unsupported-machine-target` and verifies rejection.
3. **SecurityVersion Downgrade Rejection**: Generates and uploads a synthetic tarball with `SecurityVersion=0` and verifies anti-rollback rejection.

---

### 3.3 Watchdog Boot Fallback (`test-boot-fallback.sh`)

Simulates repeated boot failures to verify U-Boot's `altbootcmd` automatic bank fallback.

```bash
./test-boot-fallback.sh numaker-iot-ma35d03f80.local root:0penBmc
```

**Test Flow**:
1. Records the currently active bank (e.g., Bank A).
2. Sets U-Boot variables over SSH to simulate an unconfirmed update exceeding the boot limit (`fw_setenv bootcount 3 && fw_setenv bootlimit 3 && fw_setenv upgrade_available 1`).
3. Reboots the BMC.
4. Verifies that U-Boot falls back to the alternate bank (Bank B) and `obmc-boot-verify.service` resets `bootcount=0`.

---

## 4. Manual Redfish Update via `curl`

Run the following commands from your **Host PC**:

### Step 1: Query Current Firmware Inventory
```bash
curl -k -s -u root:0penBmc \
  https://numaker-iot-ma35d03f80.local/redfish/v1/UpdateService/FirmwareInventory | jq .
```

### Step 2: Upload Firmware Package
```bash
curl -k -s -u root:0penBmc --http1.1 \
  -X POST \
  -H "Content-Type: application/octet-stream" \
  -H "Expect:" \
  -T build-ma35/tmp/deploy/images/numaker-iot-ma35d03f80/obmc-phosphor-image-numaker-iot-ma35d03f80.mtd-ubi-tar \
  -i \
  https://numaker-iot-ma35d03f80.local/redfish/v1/UpdateService/update
```
Expected response:
```http
HTTP/1.1 202 Accepted
Location: /redfish/v1/TaskService/TaskMonitors/0
Content-Type: application/json
```

### Step 3: Monitor Task Progress
```bash
curl -k -s -u root:0penBmc \
  https://numaker-iot-ma35d03f80.local/redfish/v1/TaskService/TaskMonitors/0 | jq .
```
`PercentComplete` advances from `0` to `100` during extraction and flashing, then triggers a reboot when `ApplyTime` is `Immediate`.

### Step 4: Verify Reboot & Active Bank
```bash
# 1. Confirm Redfish Manager state
curl -k -s -u root:0penBmc https://numaker-iot-ma35d03f80.local/redfish/v1/Managers/bmc | jq .Status

# 2. Check active boot bank (SPI-NAND / Raw NAND)
ssh root@numaker-iot-ma35d03f80.local "fw_printenv bootubivol kernelname dtbname upgrade_available bootcount"

# Or check active boot bank (SD1 / eMMC)
ssh root@numaker-iot-ma35d03f80.local "cat /proc/cmdline && fw_printenv bootside upgrade_available bootcount"
```

---

## 5. Diagnostics & Troubleshooting

Log in to the BMC via serial console or SSH to inspect update status and logs.

### 5.1 Inspect D-Bus Software Manager State
```bash
# Check service status
systemctl status xyz.openbmc_project.Software.Manager.service

# List software objects and activation state
busctl tree xyz.openbmc_project.Software.Manager
busctl introspect xyz.openbmc_project.Software.Manager \
  /xyz/openbmc_project/software/<VERSION_ID> \
  xyz.openbmc_project.Software.Activation
```

### 5.2 Inspect Flash Backend Logs
Low-level partition writing and boot-pointer updates are handled by [`obmc-flash-bmc`](file:///usr/bin/obmc-flash-bmc).

- **Persistent Flash Log (survives reboot)**:
  ```bash
  cat /var/persist/flash.log
  ```
- **Live Journal Stream During Update**:
  ```bash
  journalctl -f | grep "MA35-FLASH"
  ```
