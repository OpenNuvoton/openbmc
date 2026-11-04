# MA35 OpenBMC deployment

Ported from `NuWriter/tools/autodeploy` into this OpenBMC repository.
All deployment Python, tests, and dependency declarations live here. The
Actions entry point is `../../workflows/nuwriter-deploy.yml`; GitHub requires workflow
YAML files directly under `.github/workflows`.

Python 3.10+ is supported on Windows, Linux, and macOS. Run the following
commands from the OpenBMC repository root, using `python3` if necessary.

## Install and inspect

```console
python -m pip install -r .github/scripts/nuwriter/requirements.txt
python -B -m unittest discover -s .github/scripts/nuwriter -p test_deploy.py -v
python .github/scripts/nuwriter/deploy.py deploy --prebuilt-root /path/to/images --list-only
```

Tests and `--list-only` require only the standard library. They do not
require a NuWriter checkout, USB, UART, reset hooks, or board writes.

The NuWriter runtime is bundled beside `deploy.py`: `nuwriter.py`, its
Python modules, `xusb.bin`, and `ddrimg/ddr_auto.bin`. No runtime path
argument or repository variable is required. NuWriter runs with this
directory as its working directory and the same Python interpreter as
the deployment tool, independently of the current working directory.

For an optional external runtime, set `MA35_NUWRITER_ROOT` or pass
`--nuwriter-root`. WSL/Linux requires Linux runtime paths and USB/UART
access within Linux; do not use a Windows `C:\...` path as a Linux path.

Without an explicit image directory, the tool uses
`artifacts/openbmc-<machine>` under the OpenBMC repository root.
Select `numaker-iot-ma35d03f80` (default), `numaker-iot-ma35d05ki1`, or
`numaker-iot-ma35d16fj87c` using `--machine` or `MA35_MACHINE`. All three
use `ddrimg/ddr_auto.bin` for DDR initialization during flashing and
native boot. For example:

```console
python .github/scripts/nuwriter/deploy.py deploy --machine numaker-iot-ma35d16fj87c --list-only
```

Reports default to `autodeploy-results` under that root, independently of
the current working directory. `MA35_PREBUILT_ROOT` overrides the image
default, and CLI options override environment settings.

## Hardware configuration

Flashing erases or overwrites storage. Use a dedicated DUT with the intended
NAND, SPI-NAND, and SD storage fitted, and isolate other boards. The tool
rejects anything other than exactly one USB download device `0416:5963`.
Reserve the UART and reset jig for this runner. The selected machine must
match the physically connected DUT; the USB device ID does not identify
the board model. No automatic multi-board deployment is enabled.

Provision PyUSB's libusb backend and device access for the selected OS:

- Windows: NuWriter WinUSB driver and a libusb DLL accessible to Python.
- Linux: libusb and appropriate USB/serial permissions.
- macOS: libusb and access to the board's USB and serial devices.

| Environment variable | CLI option | Meaning |
|---|---|---|
| `MA35_MACHINE` | `--machine` | Selected MA35 machine; defaults to `numaker-iot-ma35d03f80` |
| `MA35_NUWRITER_ROOT` | `--nuwriter-root` | Optional runtime override; defaults to the directory containing `deploy.py` |
| `MA35_PREBUILT_ROOT` | `--prebuilt-root` | Trusted extracted image directory |
| `MA35_SERIAL_PORT` | `--serial-port` | DUT UART, e.g. `COM3` or `/dev/ttyUSB0` |
| - | `--download-hook` | Optional CLI override; defaults to the bundled `download_hook.py` |
| - | `--boot-script` | Optional CLI-only noninteractive boot override |
| `MA35_BOOT_DTB` | `--boot-dtb` | Optional DTB override; defaults to the matching BL2/DTB pair in the prebuilt directory |
| `MA35_BOOT_BL2` | `--boot-bl2` | Optional matching custom BL2 override; specify both overrides together |

No download or boot hook environment variables are required or read.
For manual CLI use, `--boot-batch` remains an alias of `--boot-script`;
an explicit boot script takes precedence over the native boot images.

Validate configuration without opening UART, resetting, or flashing:

```console
python .github/scripts/nuwriter/deploy.py check-runner
```

### Download-mode hook

Deployment automatically calls `download_hook.py` beside `deploy.py`
using the runner's current Python, before every case and after failures.
It passes the medium, deploy option, and serial port, for example:

```console
python .github/scripts/nuwriter/download_hook.py --media sd --deploy-option 7 --serial-port /dev/ttyUSB0
```

The bundled hook is a placeholder: it prints `download_hook hello` and
returns successfully. It does not change pins, reset or power-cycle the
DUT, or wait for USB enumeration. Implement the lab-specific controls in
this file before unattended hardware deployment. A real hook must enter
download mode and return zero only on success; do not prompt or detach
reset operations into the background. No reset wiring is guessed.

For optional CLI hook overrides, Python hooks use the current interpreter.
Native executables use the same
long options. POSIX `.sh` hooks are supported on Linux/macOS, and `.bat` or
`.cmd` hooks on Windows. `.ps1` hooks require PowerShell and receive legacy
parameters `-Media sd -DeployOption 7 -SerialPort COM3`.

### Boot configuration

The workflow uses native boot by default. For manual CLI use, choose one method:

1. Provide a boot hook that receives one numeric positional argument
   (`3`, `5`, or `7`), boots the flashed medium, and exits nonzero on failure.
   An existing Windows `deploy.bat` may be selected explicitly.
2. For native boot, include one matching `bl2-<platform>.dtb` and
   `bl2-<platform>.bin` pair in the prebuilt directory. Discovery is
   recursive and requires both files in the same directory with the same
   stem; missing or ambiguous pairs fail before hardware operations.
   `bl2.dtb` and `bl2.bin` are also supported. To use external boot images,
   provide both `--boot-dtb` and `--boot-bl2`. Python writes the medium
   selector at `0x2803FFFC`, writes the DTB at `0x28023000`, and
   loads/executes BL2 at `0x28000000`.

| Medium | Boot option | SRAM selector |
|---|---|---|
| SPI-NAND 1-bit | `3` | `0x00000000` |
| NAND | `5` | `0x00000800` |
| SD/eMMC 1 | `7` | `0x00004400` |

Native boot requires xusb register-command support and matching custom BL2
that consumes/reserves this SRAM word and handles cache visibility. Stock
BL2 does not automatically use it. Image-size checks prevent direct image
overlap but cannot verify runtime stack/BSS placement. Read-only power-on
setting registers are not written. A physical-boot-pin jig may instead
provide a boot hook.

After implementing the download hook and configuring UART:

```console
python .github/scripts/nuwriter/deploy.py deploy --prebuilt-root /path/to/images
```

## Discovery and results

The scanner recursively recognizes `nuwriter_program_sd.bat`,
`nuwriter_program_nand.bat`, and `nuwriter_program_spinand.bat`. Each needs a
sibling `nuwriter-pack-<media>-<machine>.bin` for the selected machine. All cases are
validated before the first hardware action. Installed `MA35D1_NuWriter`
directories, symbolic links, junctions, and installer scripts are skipped.

Batch files identify cases; they are never executed or parsed. The planner
initializes DDR with `-a ddrimg/ddr_auto.bin`, erases NAND/SPI-NAND with
`-e <media> all`, then writes the pack using `-w <media> <pack>` (`emmc` for
SD). Source scripts and images are never modified.

Each case enters download mode, flashes, opens a fresh UART capture, and
requires the ordered `BL2:` -> `U-Boot` -> `Linux version` ->
`<machine> login:` sequence. Assertions, synchronous aborts,
unsupported boot interfaces, and kernel panics fail the case, even after
login. Failed cases do not prevent subsequent cases from running. Any
failure produces exit code 1.

Options include `--output-directory`, `--boot-timeout-seconds` (600),
`--observe-seconds` (10 after login), `--flash-timeout-seconds` (1800),
`--hook-timeout-seconds` (120), and `--baud-rate` (115200, UART 8N1).
Commands receive no stdin, have bounded deadlines, and have their process
tree/group terminated on timeout.

Reports include `results.json`, `junit.xml`, and numbered case directories
with command stdout/stderr, `usb.json`, and raw `uart.log`. Artifact
resolution also writes `source.json` provenance. Both JSON reports record
the selected machine. Results are saved after
each case. The `summary` subcommand publishes the results to
`GITHUB_STEP_SUMMARY` when configured.

## GitHub Actions

Run **NuWriter deployment** manually. This port does not enable scheduled
flashing or modify the existing `numaker.yml` build. `list_only` defaults
to true; explicitly disable it to control hardware.

Choose the `machine` matching the DUT from the three MA35 options. The
workflow downloads only `openbmc-<machine>`, sets `MA35_MACHINE`, and names
the uploaded test reports with the selected machine. NUC980 and an `all`
option are not supported by this hardware deployment workflow.

The deployment job uses `[self-hosted]` and the `ma35-hardware` environment,
including for listing. It uses the runner's existing Python without a
version matrix or Python installation step. Provision Python 3.10+ and
dependencies first, and configure the hardware variables in the table
above as repository or environment variables. The workflow uses the
bundled NuWriter runtime without a `MA35_NUWRITER_ROOT` variable. Use
absolute paths outside the checkout for local images and lab hooks because
checkout cleanup may remove untracked files within the workspace. Commit
the bundled runtime files so they are available after checkout.

`numaker.yml` includes the TF-A BL2 binary and DTB in each machine's
artifact. The deployment workflow checks hardware configuration after
downloading the artifact and resolves both files from that prebuilt
directory; no `MA35_BOOT_DTB` or `MA35_BOOT_BL2` GitHub variables are needed.
Local image directories use the same discovery rules. Previously uploaded
artifacts must already contain the boot pair; changing the upload list
does not add files to older artifacts.

Protect the hardware environment and trusted workflow code. Concurrency
group `hardware-flash-banana` serializes this repository's runs only; it
cannot lock manual processes or another repository's hardware job.

Select `artifact` or `local` as the image source. Artifact mode selects an
approved successful `OpenNuvoton/openbmc` `numaker.yml` run on the branch
configured by `OPENBMC_BRANCH`, with a non-expired
`openbmc-<machine>` artifact matching the selected machine. Supply a run ID
or let it search the latest ten successful runs. Fork/PR runs are rejected.
Local mode uses `MA35_PREBUILT_ROOT` and does not request upstream artifacts.

The workflow uses `GITHUB_TOKEN` by default. When cross-repository artifact
access requires it, configure the optional `OPENBMC_ARTIFACT_TOKEN` secret
with upstream Actions-read permission. Never put tokens in CLI arguments,
hooks, or ordinary variables. The workflow publishes a summary and uploads
reports even on failure, with 14-day retention.