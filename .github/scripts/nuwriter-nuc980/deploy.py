"""Discover and test trusted NUC980 OpenBMC prebuilt images."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from typing import Any
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_NUWRITER_ROOT = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_HOOK = Path(__file__).resolve().with_name('download_hook.py')
DEFAULT_BOOT_HOOK = Path(__file__).resolve().with_name('boot_hook.py')
DEFAULT_MACHINE = 'numaker-iot-nuc980g2'
SUPPORTED_MACHINES = (
    'numaker-iot-nuc980g2',
)
DDR_CONFIG = 'NUC980DK71YC.ini'
DEFAULT_PREBUILT_ROOT = REPO_ROOT / 'artifacts' / f'openbmc-{DEFAULT_MACHINE}'
DEFAULT_OUTPUT_DIRECTORY = REPO_ROOT / 'autodeploy-results'
DEPLOY_OPTIONS = {'spinand': 4, 'sd': 7}
BOOT_MARKERS = ('U-Boot', 'Linux version', f'{DEFAULT_MACHINE} login:')
BOOT_FAILURE = re.compile(
    r'^\s*ASSERT:|Kernel panic|Synchronous Abort|ERROR:\s+Boot interface'
    r'|^\s*(?:NUC980[>#]|=>)',
    re.IGNORECASE | re.MULTILINE,
)

ANSI_RESET = '\033[0m'
ANSI_BOLD = '\033[1m'
ANSI_DIM = '\033[2m'
STORAGE_COLORS = {
    'sd': '\033[1;35m',       # Bold Magenta
    'spinand': '\033[1;33m',  # Bold Yellow
}
PHASE_COLORS = {
    'download-mode': '\033[1;34m',  # Bold Blue
    'flash': '\033[1;35m',          # Bold Magenta
    'boot': '\033[1;36m',           # Bold Cyan
    'test': '\033[1;33m',           # Bold Yellow
    'complete': '\033[1;32m',       # Bold Green
}
STATUS_COLORS = {
    'passed': '\033[1;32m',  # Bold Green
    'failed': '\033[1;31m',  # Bold Red
}


def storage_badge(media: str) -> str:
    color = STORAGE_COLORS.get(media.lower(), ANSI_BOLD)
    return f'{color}[STORAGE: {media.upper()}]{ANSI_RESET}'


def phase_badge(phase: str, detail: str = '') -> str:
    color = PHASE_COLORS.get(phase.lower(), ANSI_BOLD)
    label = f'{phase.upper()}: {detail}' if detail else phase.upper()
    return f'{color}[PHASE: {label}]{ANSI_RESET}'


def log_case_banner(index: int, total: int, case: DeploymentCase) -> None:
    color = STORAGE_COLORS.get(case.media.lower(), ANSI_BOLD)
    border = f'{color}{"=" * 80}{ANSI_RESET}'
    print(
        f'\n{border}\n'
        f'{color}[{index}/{total}]{ANSI_RESET} {storage_badge(case.media)} '
        f'{ANSI_BOLD}{case.name}{ANSI_RESET} '
        f'{ANSI_DIM}(machine={case.machine}, image={case.image.name}){ANSI_RESET}\n'
        f'{border}',
        flush=True,
    )


def log_phase_banner(media: str, phase: str, message: str, detail: str = '') -> None:
    color = PHASE_COLORS.get(phase.lower(), ANSI_BOLD)
    line = f'{color}{"-" * 80}{ANSI_RESET}'
    print(
        f'\n{line}\n'
        f'{storage_badge(media)} {phase_badge(phase, detail)} {ANSI_BOLD}{message}{ANSI_RESET}\n'
        f'{line}',
        flush=True,
    )


def infer_log_badges(log_prefix: Path) -> str:
    parent_match = re.search(r'_(sd|spinand)$', log_prefix.parent.name, re.IGNORECASE)
    media = parent_match.group(1).lower() if parent_match else ''
    step = log_prefix.name.lower()
    if step == 'reset':
        phase = 'download-mode'
    elif step.startswith('flash-'):
        phase = 'flash'
    elif step.startswith('boot-'):
        phase = 'boot'
    elif step.startswith('test-'):
        phase = 'test'
    else:
        phase = ''
    badges = []
    if media:
        badges.append(storage_badge(media))
    if phase:
        badges.append(phase_badge(phase))
    return (' '.join(badges) + ' ') if badges else ''


def machine_name(value: str) -> str:
    if value not in SUPPORTED_MACHINES:
        raise ValueError(f'Unsupported NUC980 machine: {value}')
    return value


def prebuilt_directory(args: argparse.Namespace) -> Path:
    return args.prebuilt_root or REPO_ROOT / 'artifacts' / f'openbmc-{machine_name(args.machine)}'


@dataclass(frozen=True)
class DeploymentCase:
    name: str
    media: str
    script: Path
    image: Path
    deploy_option: int
    machine: str = DEFAULT_MACHINE

    def to_dict(self) -> dict:
        return {key: str(value) if isinstance(value, Path) else value
                for key, value in asdict(self).items()}


def is_link(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), 'st_file_attributes', 0)
    except OSError:
        return False
    return path.is_symlink() or bool(attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def discover_cases(root: Path, machine: str = DEFAULT_MACHINE) -> list[DeploymentCase]:
    machine_name(machine)
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f'Prebuilt root is not a directory: {root}')
    if (root / machine).is_dir() and not is_link(root / machine):
        root = (root / machine).resolve(strict=True)
    scripts = []
    for directory, children, filenames in os.walk(root, followlinks=False):
        children[:] = [name for name in children
                       if name not in {'NUC980_PyNuWriter', '.git', '__pycache__'} and not re.fullmatch(r'\d{4}-\d{12}|conv(?:-[^/\\]+)?|pack(?:-[^/\\]+)?', name)
                       and not is_link(Path(directory) / name)]
        for filename in filenames:
            if re.fullmatch(r'nuwriter_program_(sd|spinand)\.bat', filename, re.IGNORECASE):
                path = Path(directory) / filename
                if not is_link(path):
                    scripts.append(path)
    if not scripts:
        raise ValueError(f'No supported nuwriter_program_*.bat files found under {root}')
    cases = []
    for script in sorted(scripts, key=lambda path: str(path).casefold()):
        media = script.stem.rsplit('_', 1)[1].lower()
        if media == 'spinand':
            candidates = [
                script.parent / f'nuwriter-pack-spinand-{machine}.bin',
                script.parent / f'nuwriter-pack-{machine}.bin',
                script.parent / 'nuwriter-pack.bin',
            ]
            image = None
            for cand in candidates:
                if cand.is_file() and not is_link(cand):
                    image = cand
                    break
            if image is None:
                raise ValueError(f'Missing regular image for {script}: {candidates[0]}')
        elif media == 'sd':
            candidates = [
                script.parent / f'nuwriter-pack-sd-{machine}.bin',
                script.parent / 'nuwriter-pack-sd.bin',
            ]
            image = None
            for cand in candidates:
                if cand.is_file() and not is_link(cand):
                    image = cand
                    break
            if image is None:
                images = [path for path in script.parent.glob(f'obmc-phosphor-image-{machine}*.wic')
                          if path.is_file() and not is_link(path)]
                canonical = script.parent / f'obmc-phosphor-image-{machine}.wic'
                if canonical in images:
                    image = canonical
                elif is_link(canonical) and canonical.resolve() in images:
                    image = canonical.resolve()
                elif len(images) == 1:
                    image = images[0]
                elif len(images) > 1:
                    raise ValueError(f'Ambiguous SD WIC images for {script}: '
                                     + ', '.join(str(path) for path in sorted(images)))
            if image is None or not image.is_file() or is_link(image):
                expected = f'nuwriter-pack-sd-{machine}.bin or obmc-phosphor-image-{machine}*.wic'
                raise ValueError(f'Missing regular image for {script}: {expected}')
        else:
            raise ValueError(f'Unsupported media for {script}: {media}')
        cases.append(DeploymentCase(script.stem, media, script, image, DEPLOY_OPTIONS[media], machine))
    return cases


def script_command(path: Path, arguments: list[str], platform: str | None = None) -> list[str]:
    platform = platform or sys.platform
    path = path.resolve(strict=True)
    suffix = path.suffix.lower()
    if suffix == '.py':
        return [sys.executable, str(path), *arguments]
    if suffix in {'.bat', '.cmd'}:
        if platform != 'win32':
            raise ValueError(f'Windows batch cannot run on {platform}; provide a Python/native hook: {path}')
        if any(re.search(r'[&|<>^%!"\r\n]', value) for value in [str(path), *arguments]):
            raise ValueError('Unsafe shell characters in Windows hook path or arguments')
        command = ' '.join(f'"{value}"' for value in [str(path), *arguments])
        return [os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/v:off', '/s', '/c', f'"{command}"']
    if suffix == '.ps1':
        shell = shutil.which('pwsh') or (shutil.which('powershell') if platform == 'win32' else None)
        if not shell:
            raise ValueError('A .ps1 hook requires PowerShell; prefer a .py hook for portability')
        return [shell, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(path), *arguments]
    if suffix == '.sh':
        if platform == 'win32':
            raise ValueError('Use a .py/native hook on Windows instead of a .sh hook')
        return ['/bin/sh', str(path), *arguments]
    return [str(path), *arguments]


def download_command(path: Path, case: DeploymentCase, port: str) -> list[str]:
    flags = ('-Media', '-DeployOption', '-SerialPort') if path.suffix.lower() == '.ps1' else (
        '--media', '--deploy-option', '--serial-port')
    return script_command(path, [flags[0], case.media, flags[1], str(case.deploy_option), flags[2], port])


def boot_command(path: Path, case: DeploymentCase, port: str) -> list[str]:
    flags = ('-Media', '-DeployOption', '-SerialPort') if path.suffix.lower() == '.ps1' else (
        '--media', '--deploy-option', '--serial-port')
    return script_command(path, [str(case.deploy_option), flags[0], case.media, flags[1], str(case.deploy_option), flags[2], port])


def nuwriter_command(root: Path, *arguments: str) -> list[str]:
    return [sys.executable, str(root / 'nuwriter.py'), *arguments]


def flash_commands(root: Path, case: DeploymentCase) -> list[list[str]]:
    machine_name(case.machine)
    commands = [nuwriter_command(root, '-a', DDR_CONFIG)]
    if case.media == 'spinand':
        commands.append(nuwriter_command(root, '-e', 'spinand', 'all'))
        commands.append(nuwriter_command(root, '--ddr', DDR_CONFIG, '-w', 'spinand', str(case.image)))
    elif case.media == 'sd':
        if case.image.suffix.lower() == '.wic':
            commands.append(nuwriter_command(root, '-w', 'sd', '0x0', str(case.image)))
        else:
            commands.append(nuwriter_command(root, '--ddr', DDR_CONFIG, '-w', 'sd', str(case.image)))
    return commands


def boot_image_entry_address(image: Path) -> str:
    if 'spl' in image.name.lower():
        return '0x200'
    return '0x00e00000'


def discover_boot_image(case: DeploymentCase) -> Path:
    machine_name(case.machine)
    parent = case.script.parent
    machine = case.machine
    if case.media == 'sd':
        candidates = [
            parent / f'u-boot-sd-{machine}.bin',
            parent / 'u-boot-sd.bin',
        ]
    elif case.media == 'spinand':
        candidates = [
            parent / f'u-boot-spl-{machine}.bin',
            parent / f'u-boot-spl.bin-{machine}',
            parent / f'u-boot-spl-{machine}',
            parent / 'u-boot-spl.bin',
            parent / 'u-boot-spl',
            parent / f'u-boot-spinand-{machine}.bin',
            parent / f'u-boot-{machine}.bin',
            parent / 'u-boot-spinand.bin',
            parent / 'u-boot.bin',
        ]
    else:
        raise ValueError(f'Unsupported media for boot image: {case.media}')

    for cand in candidates:
        if cand.is_file():
            target = cand.resolve() if is_link(cand) else cand
            if target.is_file():
                return target

    if case.media == 'sd':
        matches = [p for p in parent.glob(f'*u-boot-sd*{machine}*.bin')
                   if not is_link(p) and p.is_file()]
    else:
        spl_matches = [p for p in parent.glob(f'*u-boot-spl*{machine}*')
                       if not is_link(p) and p.is_file()]
        if len(spl_matches) == 1:
            return spl_matches[0]
        elif len(spl_matches) > 1:
            bin_matches = [p for p in spl_matches if p.suffix == '.bin' or '.bin' in p.name]
            if len(bin_matches) == 1:
                return bin_matches[0]
            raise ValueError(f'Ambiguous U-Boot SPL boot images for {case.script}: '
                             + ', '.join(str(p) for p in sorted(spl_matches)))

        matches = [p for p in parent.glob(f'*u-boot*{machine}*.bin')
                   if not is_link(p) and p.is_file() and 'sd' not in p.name.lower() and 'spl' not in p.name.lower()]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        raise ValueError(f'Ambiguous U-Boot boot images for {case.script}: '
                         + ', '.join(str(p) for p in sorted(matches)))

    raise ValueError(f'Missing regular U-Boot boot image for {case.script} (media={case.media})')


def native_boot_commands(root: Path, case: DeploymentCase, uboot: Path) -> list[list[str]]:
    machine_name(case.machine)
    address = boot_image_entry_address(uboot)
    return [
        nuwriter_command(root, '-a', DDR_CONFIG, '-w', 'ddr', address, str(uboot), '-o', 'execute')
    ]


def post_boot_test_commands(case: DeploymentCase, bmc_host: str,
                            doc_root: Path | None = None) -> list[tuple[str, list[str]]]:
    machine_name(case.machine)
    base = (doc_root or (REPO_ROOT / 'meta-numaker' / 'doc')) / case.machine
    tests: list[tuple[str, list[str]]] = []
    redfish = base / 'test-redfish.sh'
    if redfish.is_file() and not is_link(redfish):
        tests.append(('test-01-redfish', ['/bin/bash', str(redfish), bmc_host]))
    return tests


def boot_complete(text: str, machine: str = DEFAULT_MACHINE) -> bool:
    machine_name(machine)
    failure = BOOT_FAILURE.search(text)
    if failure:
        raise RuntimeError(f'Boot failure detected: {failure.group(0)}')
    position = 0
    for marker in (*BOOT_MARKERS[:-1], f'{machine} login:'):
        position = text.find(marker, position)
        if position < 0:
            return False
        position += len(marker)
    return True


class SerialCapture:
    def __init__(self, console: Any, log_path: Path, machine: str = DEFAULT_MACHINE, echo: bool = True):
        self.console = console
        self.log_path = log_path
        self.machine = machine_name(machine)
        self.echo = echo
        self.data = bytearray()
        log_path.write_bytes(b'')

    def drain(self, block: bool = False) -> None:
        size = self.console.in_waiting
        if size or block:
            data = self.console.read(size or 1)
            if data:
                self.data.extend(data)
                with self.log_path.open('ab') as stream:
                    stream.write(data)
                if self.echo:
                    sys.stdout.write(data.decode('utf-8', errors='replace'))
                    sys.stdout.flush()

    @property
    def text(self) -> str:
        return self.data.decode('utf-8', errors='replace')


def flush_log_stream(reader: Any, destination: Any) -> None:
    chunk = reader.read()
    if chunk:
        destination.write(chunk.decode('utf-8', errors='replace'))
        destination.flush()


def terminate_process_tree(process: subprocess.Popen) -> None:
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=15, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=10)


def run_process(command: list[str], cwd: Path, log_prefix: Path, timeout: float,
                capture: SerialCapture | None = None, echo: bool = True,
                env: dict[str, str] | None = None) -> str:
    if timeout <= 0:
        raise TimeoutError('Process deadline already expired')
    stdout_path = log_prefix.with_name(log_prefix.name + '.stdout.log')
    stderr_path = log_prefix.with_name(log_prefix.name + '.stderr.log')
    process_command: list[str] | str = command
    if os.name == 'nt' and Path(command[0]).name.lower() == 'cmd.exe' and command[-2].lower() == '/c':
        process_command = subprocess.list2cmdline(command[:-1]) + ' ' + command[-1]
    if echo:
        badges = infer_log_badges(log_prefix)
        print(f'\n{ANSI_BOLD}==>{ANSI_RESET} {badges}{ANSI_BOLD}[{log_prefix.name}]{ANSI_RESET} {" ".join(command)}', flush=True)
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr, \
            stdout_path.open('rb') as stdout_reader, stderr_path.open('rb') as stderr_reader:
        process = subprocess.Popen(
            process_command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            env=process_env,
            start_new_session=os.name != 'nt',
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        deadline = time.monotonic() + timeout
        try:
            while True:
                if echo:
                    flush_log_stream(stdout_reader, sys.stdout)
                    flush_log_stream(stderr_reader, sys.stderr)
                if capture:
                    capture.drain()
                    boot_complete(capture.text, capture.machine)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f'Process timed out after {timeout:g}s: {command[0]} (see {log_prefix}.*.log)')
                try:
                    process.wait(timeout=min(0.1, remaining))
                    break
                except subprocess.TimeoutExpired:
                    continue
            if capture:
                capture.drain()
                boot_complete(capture.text, capture.machine)
            if process.returncode:
                raise RuntimeError(f'Process exited with code {process.returncode}: {command[0]} (see {log_prefix}.*.log)')
        except BaseException:
            if process.poll() is None:
                terminate_process_tree(process)
            raise
        finally:
            if echo:
                flush_log_stream(stdout_reader, sys.stdout)
                flush_log_stream(stderr_reader, sys.stderr)
    return stdout_path.read_text(encoding='utf-8', errors='replace')


def wait_for_boot(capture: SerialCapture, deadline: float, observe_seconds: float,
                  machine: str = DEFAULT_MACHINE) -> None:
    healthy_at = None
    while time.monotonic() < deadline:
        capture.drain(block=True)
        if boot_complete(capture.text, machine):
            if healthy_at is None:
                healthy_at = time.monotonic()
            if time.monotonic() - healthy_at >= observe_seconds:
                return
    raise TimeoutError(f'Boot did not reach a healthy OpenBMC login before the deadline. See {capture.log_path}')


def check_dependencies() -> None:
    for module in ('usb.core', 'serial', 'serial.tools.list_ports'):
        try:
            importlib.import_module(module)
        except ImportError as error:
            requirements = Path(__file__).with_name('requirements.txt')
            raise ValueError(f'Missing dependency {module}; install {requirements}') from error


def available_serial_ports() -> list[str]:
    from serial.tools import list_ports
    return [port.device for port in list_ports.comports()]


def open_console(port: str, baud_rate: int) -> Any:
    import serial
    return serial.Serial(port, baud_rate, timeout=0.1)


def device_count() -> int:
    import usb.core
    return len(list(usb.core.find(find_all=True, idVendor=0x0416, idProduct=0x5963)))


def validate_configuration(args: argparse.Namespace) -> None:
    machine_name(args.machine)
    check_dependencies()
    args.nuwriter_root = (args.nuwriter_root or DEFAULT_NUWRITER_ROOT).resolve(strict=True)
    for filename in ('nuwriter.py', f'sys_cfg/{DDR_CONFIG}'):
        if not (args.nuwriter_root / filename).is_file():
            raise ValueError(f'Missing NuWriter runtime file: {filename}')
    if not (args.nuwriter_root / 'xusb').is_dir():
        raise ValueError('Missing NuWriter xusb runtime directory')
    if not args.download_hook:
        raise ValueError('Configure --download-hook before deployment')
    try:
        args.download_hook = Path(args.download_hook).resolve(strict=True)
    except OSError:
        raise ValueError('Download hook must be a file')
    if not args.download_hook.is_file():
        raise ValueError('Download hook must be a file')
    script_command(args.download_hook, [])
    if not args.serial_port or args.serial_port not in available_serial_ports():
        raise ValueError(f'Unavailable DUT UART port: {args.serial_port!r}')
    if args.boot_script:
        try:
            args.boot_script = Path(args.boot_script).resolve(strict=True)
        except OSError:
            raise ValueError('Boot hook must be a file')
        if not args.boot_script.is_file():
            raise ValueError('Boot hook must be a file')
        script_command(args.boot_script, [])
    else:
        cases = discover_cases(prebuilt_directory(args), args.machine)
        for case in cases:
            uboot = discover_boot_image(case)
            if not uboot.is_file() or uboot.stat().st_size == 0 or uboot.stat().st_size > 0x1000000:
                raise ValueError(f'Invalid or missing U-Boot boot image for {case.name}: {uboot}')


def write_results(results: list[dict], output: Path) -> None:
    (output / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    suite = ET.Element('testsuite', name='NUC980 OpenBMC prebuilt deployment', tests=str(len(results)),
                       failures=str(sum(result['status'] == 'failed' for result in results)))
    for result in results:
        case = ET.SubElement(suite, 'testcase', name=result['name'], classname=result['media'], time=str(result['seconds']))
        if result['status'] == 'failed':
            ET.SubElement(case, 'failure', message=result['error']).text = result['error']
    ET.ElementTree(suite).write(output / 'junit.xml', encoding='utf-8', xml_declaration=True)


def deploy_cases(args: argparse.Namespace) -> int:
    cases = discover_cases(prebuilt_directory(args), args.machine)
    if args.list_only:
        print(json.dumps([case.to_dict() for case in cases], indent=2))
        return 0
    validate_configuration(args)
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for index, case in enumerate(cases, start=1):
        log_case_banner(index, len(cases), case)
        directory = output / f'{index:02d}-{case.name}'
        directory.mkdir(parents=True, exist_ok=True)
        result = {**case.to_dict(), 'status': 'failed', 'phase': 'download-mode', 'seconds': 0.0, 'error': ''}
        started = time.monotonic()
        console = None
        try:
            log_phase_banner(case.media, 'download-mode',
                             f'Switching {case.machine} into USB download mode ({args.serial_port})')
            run_process(download_command(args.download_hook, case, args.serial_port), case.script.parent,
                        directory / 'reset', args.hook_timeout_seconds)
            count = device_count()
            (directory / 'usb.json').write_text(json.dumps({'count': count}), encoding='utf-8')
            if count != 1:
                raise RuntimeError(f'Expected exactly one NuWriter DUT; detected {count}. Isolate the other board before flashing.')
            result['phase'] = 'flash'
            log_phase_banner(case.media, 'flash',
                             f'Programming {case.image.name} to {case.media.upper()}')
            flash_deadline = time.monotonic() + args.flash_timeout_seconds
            flash_env = {'NUWRITER_SKIP_PRE_ATTACH_HOOK': '1'}
            for step, command in enumerate(flash_commands(args.nuwriter_root, case), start=1):
                run_process(command, args.nuwriter_root, directory / f'flash-{step:02d}',
                            flash_deadline - time.monotonic(), env=flash_env)
            result['phase'] = 'boot'
            mode_desc = 'via script' if args.boot_script else 'via NuWriter DRAM execution'
            log_phase_banner(case.media, 'boot',
                             f'Booting from {case.media.upper()} (option={case.deploy_option}) {mode_desc}')
            console = open_console(args.serial_port, args.baud_rate)
            console.reset_input_buffer()
            capture = SerialCapture(console, directory / 'uart.log', args.machine)
            deadline = time.monotonic() + args.boot_timeout_seconds
            if args.boot_script:
                commands = [boot_command(args.boot_script, case, args.serial_port)]
                cwd = args.boot_script.parent
            else:
                uboot_image = discover_boot_image(case)
                commands = native_boot_commands(args.nuwriter_root, case, uboot_image)
                cwd = args.nuwriter_root
            for step, command in enumerate(commands, start=1):
                run_process(command, cwd, directory / f'boot-{step:02d}', deadline - time.monotonic(), capture,
                            env={'NUWRITER_SKIP_PRE_ATTACH_HOOK': '1'})
            wait_for_boot(capture, deadline, args.observe_seconds, machine=args.machine)
            bmc_host = getattr(args, 'bmc_host', None) or f'{args.machine}.local'
            tests = post_boot_test_commands(case, bmc_host)
            if tests:
                result['phase'] = 'test'
                test_deadline = time.monotonic() + getattr(args, 'test_timeout_seconds', 900)
                for test_name, test_command in tests:
                    log_phase_banner(case.media, 'test',
                                     f'Running post-boot verification: {test_name}', detail=test_name)
                    run_process(test_command, REPO_ROOT, directory / test_name,
                                test_deadline - time.monotonic(), capture)
            result.update(status='passed', phase='complete')
            elapsed = round(time.monotonic() - started, 3)
            pass_color = STATUS_COLORS['passed']
            border = f'{pass_color}{"=" * 80}{ANSI_RESET}'
            print(
                f'\n{border}\n'
                f'{pass_color}[PASS]{ANSI_RESET} [{index}/{len(cases)}] {storage_badge(case.media)} '
                f'{phase_badge("complete")} {pass_color}PASSED: {case.name} ({elapsed}s){ANSI_RESET}\n'
                f'{border}',
                flush=True,
            )
        except Exception as error:
            result['error'] = str(error)
            elapsed = round(time.monotonic() - started, 3)
            fail_color = STATUS_COLORS['failed']
            border = f'{fail_color}{"=" * 80}{ANSI_RESET}'
            print(
                f'\n{border}\n'
                f'{fail_color}[FAIL]{ANSI_RESET} [{index}/{len(cases)}] {storage_badge(case.media)} '
                f'{phase_badge(result["phase"])} {fail_color}FAILED: {case.name} ({elapsed}s): {error}{ANSI_RESET}\n'
                f'{border}',
                file=sys.stderr,
                flush=True,
            )
        finally:
            if console is not None:
                try:
                    console.close()
                except Exception as error:
                    result['status'] = 'failed'
                    result['error'] += f'; UART cleanup failed: {error}'
            result['seconds'] = round(time.monotonic() - started, 3)
            results.append(result)
            write_results(results, output)
    all_passed = all(result['status'] == 'passed' for result in results)
    summary_color = STATUS_COLORS['passed'] if all_passed else STATUS_COLORS['failed']
    border = f'{summary_color}{"=" * 80}{ANSI_RESET}'
    summary_lines = [
        f'\n{border}',
        f'{summary_color}DEPLOYMENT SUMMARY ({args.machine}){ANSI_RESET}',
        f'{summary_color}{"-" * 80}{ANSI_RESET}',
    ]
    for idx, res in enumerate(results, start=1):
        st_color = STATUS_COLORS.get(res['status'], ANSI_BOLD)
        st_label = 'PASS' if res['status'] == 'passed' else 'FAIL'
        err_suffix = f' -> {STATUS_COLORS["failed"]}{res["error"]}{ANSI_RESET}' if res.get('error') else ''
        summary_lines.append(
            f'  {st_color}[{st_label}]{ANSI_RESET} [{idx}/{len(results)}] '
            f'{storage_badge(res["media"])} {phase_badge(res["phase"])} '
            f'{ANSI_BOLD}{res["name"]}{ANSI_RESET} ({res["seconds"]}s){err_suffix}'
        )
    summary_lines.append(border)
    print('\n'.join(summary_lines), flush=True)
    return int(any(result['status'] == 'failed' for result in results))


def bounded_number(minimum: int, maximum: int):
    def parse(value: str) -> int:
        number_float = float(value)
        if not number_float.is_integer():
            raise argparse.ArgumentTypeError(f'Expected an integer in [{minimum}, {maximum}]')
        number = int(number_float)
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f'Expected a number in [{minimum}, {maximum}]')
        return number
    return parse


def github_json(url: str, token: str) -> dict:
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def append_github_outputs(path: str | None, values: dict[str, str]) -> None:
    if not path:
        return
    if any('\n' in value or '\r' in value for value in values.values()):
        raise ValueError('GitHub output values cannot contain newlines')
    with Path(path).open('a', encoding='utf-8') as stream:
        for key, value in values.items():
            stream.write(f'{key}={value}\n')


def resolve_source(workspace: Path, environment=None, request_json=None,
                   machine: str | None = None) -> dict[str, str]:
    environment = os.environ if environment is None else environment
    request_json = github_json if request_json is None else request_json
    machine = machine_name(machine or environment.get('NUC980_MACHINE') or DEFAULT_MACHINE)
    workspace = workspace.resolve()
    output = workspace / 'autodeploy-results'
    output.mkdir(parents=True, exist_ok=True)
    mode = environment.get('SOURCE_MODE') or 'artifact'
    if mode == 'local':
        configured = environment.get('NUC980_PREBUILT_ROOT')
        if not configured:
            raise ValueError('Set NUC980_PREBUILT_ROOT for local images')
        root = Path(configured).resolve(strict=True)
        if not root.is_dir():
            raise ValueError('NUC980_PREBUILT_ROOT must be a directory')
        if (root / machine).is_dir() and not is_link(root / machine):
            root = (root / machine).resolve(strict=True)
        values = {'prebuilt_root': str(root)}
        provenance = {'source': 'local', 'directory': str(root), 'machine': machine}
    elif mode == 'artifact':
        repository = environment.get('OPENBMC_REPOSITORY') or 'OpenNuvoton/openbmc'
        branch = environment.get('OPENBMC_BRANCH') or 'numaker'
        workflow_name = environment.get('OPENBMC_WORKFLOW') or 'numaker.yml'
        artifact_name = environment.get('OPENBMC_ARTIFACT') or f'openbmc-{machine}'
        token = environment.get('ARTIFACT_TOKEN', '')
        api = f'https://api.github.com/repos/{repository}/actions'
        workflow = request_json(f'{api}/workflows/{workflow_name}', token)
        run_id = environment.get('SOURCE_RUN_ID', '')
        if run_id:
            if not re.fullmatch(r'[1-9][0-9]*', run_id):
                raise ValueError('run_id must be a positive integer')
            runs = [request_json(f'{api}/runs/{run_id}', token)]
        else:
            runs = request_json(
                f'{api}/workflows/{workflow_name}/runs?status=success&branch={branch}&per_page=10', token
            ).get('workflow_runs', [])
        selected = None
        for candidate in runs:
            approved = (
                candidate.get('workflow_id') == workflow.get('id')
                and candidate.get('status') == 'completed'
                and candidate.get('conclusion') == 'success'
                and candidate.get('head_branch') == branch
                and (candidate.get('head_repository') or {}).get('full_name') == repository
                and candidate.get('event') in {'push', 'schedule', 'workflow_dispatch'}
            )
            if not approved:
                if run_id:
                    raise ValueError('The requested run is not an approved successful upstream build')
                continue
            artifacts = request_json(f"{api}/runs/{candidate['id']}/artifacts?per_page=100", token)
            matches = [artifact for artifact in artifacts.get('artifacts', [])
                       if artifact.get('name') == artifact_name and artifact.get('expired') is False]
            if len(matches) == 1:
                selected = (candidate, matches[0])
                break
        if selected is None:
            raise ValueError(f'No approved build with a non-expired {artifact_name} artifact was found')
        run, artifact = selected
        values = {
            'run_id': str(run['id']), 'artifact_id': str(artifact['id']),
            'prebuilt_root': str(workspace / 'artifacts' / f'openbmc-{machine}'),
        }
        provenance = {'source': repository, 'run_id': run['id'], 'commit': run['head_sha'],
                      'artifact_id': artifact['id'], 'machine': machine}
    else:
        raise ValueError(f'Unsupported prebuilt source: {mode}')
    append_github_outputs(environment.get('GITHUB_OUTPUT'), values)
    (output / 'source.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    return values


def publish_summary(directory: Path, destination: str | None) -> str:
    result_path = directory / 'results.json'
    if result_path.is_file():
        results = json.loads(result_path.read_text(encoding='utf-8'))
        rows = ['## NUC980 deployment and boot tests', '', '| Case | Media | Status | Phase | Seconds |',
                '|---|---|---|---|---|']
        for result in results:
            rows.append('| ' + ' | '.join(str(result[key]) for key in ('name', 'media', 'status', 'phase', 'seconds')) + ' |')
        text = '\n'.join(rows) + '\n'
    else:
        text = 'No hardware test results were produced. See the scan/configuration steps.\n'
    if destination:
        with Path(destination).open('a', encoding='utf-8') as stream:
            stream.write(text)
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('deploy', 'check-runner'):
        child = commands.add_parser(command)
        child.add_argument('--machine', type=machine_name, choices=SUPPORTED_MACHINES,
                           default=os.environ.get('NUC980_MACHINE') or DEFAULT_MACHINE)
        child.add_argument('--prebuilt-root', type=Path, default=os.environ.get('NUC980_PREBUILT_ROOT') or None)
        child.add_argument('--list-only', action='store_true')
        child.add_argument('--nuwriter-root', type=Path, default=os.environ.get('NUC980_NUWRITER_ROOT') or DEFAULT_NUWRITER_ROOT)
        child.add_argument('--serial-port', default=os.environ.get('NUC980_SERIAL_PORT'))
        child.add_argument('--download-hook', type=Path, default=DEFAULT_DOWNLOAD_HOOK)
        child.add_argument('--boot-script', '--boot-batch', type=Path, default=None)
        child.add_argument('--output-directory', type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
        child.add_argument('--flash-timeout-seconds', type=bounded_number(30, 7200), default=1800)
        child.add_argument('--boot-timeout-seconds', type=bounded_number(30, 3600), default=600)
        child.add_argument('--hook-timeout-seconds', type=bounded_number(5, 600), default=120)
        child.add_argument('--observe-seconds', type=bounded_number(0, 300), default=10)
        child.add_argument('--baud-rate', type=bounded_number(1200, 4000000), default=115200)
        child.add_argument('--bmc-host', default=os.environ.get('NUC980_BMC_HOST'))
        child.add_argument('--test-timeout-seconds', type=bounded_number(30, 7200), default=900)
    source = commands.add_parser('resolve-source')
    source.add_argument('--machine', type=machine_name, choices=SUPPORTED_MACHINES,
                        default=os.environ.get('NUC980_MACHINE') or DEFAULT_MACHINE)
    source.add_argument('--workspace', type=Path, default=Path(os.environ.get('GITHUB_WORKSPACE') or REPO_ROOT))
    summary = commands.add_parser('summary')
    summary.add_argument('--output-directory', type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0].startswith('--'):
        arguments.insert(0, 'deploy')
    args = build_parser().parse_args(arguments)
    try:
        if args.command == 'resolve-source':
            print(json.dumps(resolve_source(args.workspace, machine=args.machine), indent=2))
            return 0
        if args.command == 'summary':
            print(publish_summary(args.output_directory, os.environ.get('GITHUB_STEP_SUMMARY')), end='')
            return 0
        if args.command == 'check-runner':
            validate_configuration(args)
            print('Runner configuration validated; no board writes or resets performed.')
            return 0
        return deploy_cases(args)
    except (OSError, ValueError, RuntimeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
