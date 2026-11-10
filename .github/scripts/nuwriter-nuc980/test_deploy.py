import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import sys
import time
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

import deploy


class RepositoryLayoutTests(unittest.TestCase):
    def setUp(self):
        environment = mock.patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_defaults_use_repository_images_and_bundled_runtime(self):
        root = Path(__file__).resolve().parents[3]
        self.assertEqual(deploy.REPO_ROOT, root)
        for command in ('deploy', 'check-runner'):
            args = deploy.build_parser().parse_args([command])
            self.assertEqual(deploy.prebuilt_directory(args), root / 'artifacts/openbmc-numaker-iot-nuc980g2')
            self.assertEqual(args.output_directory, root / 'autodeploy-results')
            self.assertEqual(args.nuwriter_root, Path(deploy.__file__).resolve().parent)
            self.assertEqual(args.download_hook, Path(deploy.__file__).resolve().with_name('download_hook.py'))
            self.assertIsNone(args.boot_script)
        self.assertEqual(deploy.build_parser().parse_args(['resolve-source']).workspace, root)
        self.assertEqual(deploy.build_parser().parse_args(['summary']).output_directory, root / 'autodeploy-results')

    def test_environment_paths_are_converted_to_paths(self):
        with mock.patch.dict(os.environ, {'NUC980_NUWRITER_ROOT': 'external NuWriter',
                                          'NUC980_PREBUILT_ROOT': 'local images'}):
            args = deploy.build_parser().parse_args(['deploy'])
        self.assertEqual(args.nuwriter_root, Path('external NuWriter'))
        self.assertEqual(args.prebuilt_root, Path('local images'))

    def test_cli_paths_override_environment(self):
        with mock.patch.dict(os.environ, {'NUC980_NUWRITER_ROOT': 'environment-tools',
                                          'NUC980_PREBUILT_ROOT': 'environment-images'}):
            args = deploy.build_parser().parse_args([
                'deploy', '--nuwriter-root', 'cli-tools', '--prebuilt-root', 'cli-images'])
        self.assertEqual(args.nuwriter_root, Path('cli-tools'))
        self.assertEqual(args.prebuilt_root, Path('cli-images'))

    def test_default_runtime_and_hook_validate_without_hardware(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            machine = 'numaker-iot-nuc980g2'
            (root / 'nuwriter_program_sd.bat').touch()
            (root / f'nuwriter-pack-sd-{machine}.bin').touch()
            (root / f'u-boot-sd-{machine}.bin').write_bytes(b'uboot-sd')
            with contextlib.redirect_stdout(io.StringIO()), \
                    mock.patch.object(deploy, 'check_dependencies') as dependencies, \
                    mock.patch.object(deploy, 'available_serial_ports', return_value=['fixture-uart']), \
                    mock.patch.object(deploy, 'run_process') as process, \
                    mock.patch.object(deploy, 'open_console') as console:
                self.assertEqual(deploy.main([
                    'check-runner', '--prebuilt-root', str(root), '--serial-port', 'fixture-uart']), 0)
        dependencies.assert_called_once()
        process.assert_not_called()
        console.assert_not_called()

    def test_hook_environment_variables_are_not_used(self):
        with mock.patch.dict(os.environ, {'NUC980_DOWNLOAD_HOOK': 'unused.py',
                                          'NUC980_BOOT_SCRIPT': 'unused.py', 'NUC980_BOOT_BATCH': 'unused.bat'}):
            for command in ('deploy', 'check-runner'):
                args = deploy.build_parser().parse_args([command])
                self.assertEqual(args.download_hook, deploy.DEFAULT_DOWNLOAD_HOOK)
                self.assertIsNone(args.boot_script)

    def test_defaults_do_not_depend_on_current_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(Path, 'cwd', return_value=Path(temporary)):
            args = deploy.build_parser().parse_args(['deploy'])
        self.assertEqual(deploy.prebuilt_directory(args), deploy.DEFAULT_PREBUILT_ROOT)
        self.assertEqual(args.output_directory, deploy.DEFAULT_OUTPUT_DIRECTORY)
        self.assertEqual(args.nuwriter_root, Path(deploy.__file__).resolve().parent)
        self.assertEqual(args.download_hook, Path(deploy.__file__).resolve().with_name('download_hook.py'))
        self.assertIsNone(args.boot_script)

    def test_github_workspace_overrides_source_default(self):
        with mock.patch.dict(os.environ, {'GITHUB_WORKSPACE': 'action workspace'}):
            args = deploy.build_parser().parse_args(['resolve-source'])
        self.assertEqual(args.workspace, Path('action workspace'))

    def test_missing_dependency_references_relocated_requirements(self):
        with mock.patch.object(deploy.importlib, 'import_module', side_effect=ImportError('missing')):
            with self.assertRaises(ValueError) as error:
                deploy.check_dependencies()
        self.assertIn(str(Path(deploy.__file__).with_name('requirements.txt')), str(error.exception))


class MachineTests(unittest.TestCase):
    def setUp(self):
        environment = mock.patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_cli_selects_machine_and_default_image_directory(self):
        for machine in deploy.SUPPORTED_MACHINES:
            for command in ('deploy', 'check-runner'):
                with self.subTest(machine=machine, command=command):
                    args = deploy.build_parser().parse_args([command, '--machine', machine])
                    self.assertEqual(args.machine, machine)
                    self.assertEqual(deploy.prebuilt_directory(args), deploy.REPO_ROOT / 'artifacts' / f'openbmc-{machine}')

    def test_environment_selects_machine_for_all_commands(self):
        with mock.patch.dict(os.environ, {'NUC980_MACHINE': 'numaker-iot-nuc980g2'}):
            for command in ('deploy', 'check-runner', 'resolve-source'):
                self.assertEqual(deploy.build_parser().parse_args([command]).machine, 'numaker-iot-nuc980g2')

    def test_unsupported_cli_and_environment_machines_are_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            deploy.build_parser().parse_args(['deploy', '--machine', 'numaker-iot-ma35d03f80'])
        with mock.patch.dict(os.environ, {'NUC980_MACHINE': 'numaker-iot-ma35d03f80'}), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            deploy.build_parser().parse_args(['deploy'])

    def test_supported_machines_share_ddr_ini(self):
        self.assertEqual(deploy.SUPPORTED_MACHINES, ('numaker-iot-nuc980g2',))
        self.assertEqual(deploy.DDR_CONFIG, 'NUC980DK71YC.ini')
        self.assertTrue((deploy.DEFAULT_NUWRITER_ROOT / 'sys_cfg' / deploy.DDR_CONFIG).is_file())

    def test_discovery_selects_machine_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'nuwriter_program_sd.bat').touch()
            (root / 'nuwriter_program_spinand.bat').touch()
            machine = 'numaker-iot-nuc980g2'
            (root / f'nuwriter-pack-sd-{machine}.bin').write_bytes(b'fixture-sd')
            (root / f'nuwriter-pack-spinand-{machine}.bin').write_bytes(b'fixture-spinand')
            cases = deploy.discover_cases(root, machine)
            self.assertEqual(len(cases), 2)
            self.assertEqual(cases[0].media, 'sd')
            self.assertEqual(cases[0].image.name, f'nuwriter-pack-sd-{machine}.bin')
            self.assertEqual(cases[1].media, 'spinand')
            self.assertEqual(cases[1].image.name, f'nuwriter-pack-spinand-{machine}.bin')

    def test_wrong_machine_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'nuwriter_program_sd.bat').touch()
            (root / 'nuwriter-pack-sd-other-machine.bin').write_bytes(b'fixture')
            with self.assertRaisesRegex(ValueError, 'Missing regular image'):
                deploy.discover_cases(root, 'numaker-iot-nuc980g2')

    def test_wic_discovery_selects_machine_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'nuwriter_program_sd.bat').touch()
            machine = 'numaker-iot-nuc980g2'
            (root / f'obmc-phosphor-image-{machine}-20261104.wic').write_bytes(b'disk image')
            case = deploy.discover_cases(root, machine)[0]
            self.assertEqual(case.image.name, f'obmc-phosphor-image-{machine}-20261104.wic')
            self.assertEqual(deploy.flash_commands(deploy.DEFAULT_NUWRITER_ROOT, case)[-1][2:],
                             ['-w', 'sd', '0x0', str(case.image)])

    def test_flash_commands_match_expected_sequence(self):
        root = deploy.DEFAULT_NUWRITER_ROOT
        machine = 'numaker-iot-nuc980g2'
        sd_case = deploy.DeploymentCase('nuwriter_program_sd', 'sd', root / 'sd.bat',
                                        root / f'nuwriter-pack-sd-{machine}.bin', 7, machine)
        cmds = deploy.flash_commands(root, sd_case)
        self.assertEqual(cmds[0], [sys.executable, str(root / 'nuwriter.py'), '-a', 'NUC980DK71YC.ini'])
        self.assertEqual(cmds[1], [sys.executable, str(root / 'nuwriter.py'), '--ddr', 'NUC980DK71YC.ini',
                                   '-w', 'sd', str(sd_case.image)])

        spinand_case = deploy.DeploymentCase('nuwriter_program_spinand', 'spinand', root / 'spinand.bat',
                                             root / f'nuwriter-pack-spinand-{machine}.bin', 4, machine)
        spinand_cmds = deploy.flash_commands(root, spinand_case)
        self.assertEqual(spinand_cmds[0], [sys.executable, str(root / 'nuwriter.py'), '-a', 'NUC980DK71YC.ini'])
        self.assertEqual(spinand_cmds[1], [sys.executable, str(root / 'nuwriter.py'), '-e', 'spinand', 'all'])
        self.assertEqual(spinand_cmds[2], [sys.executable, str(root / 'nuwriter.py'), '--ddr', 'NUC980DK71YC.ini',
                                           '-w', 'spinand', str(spinand_case.image)])

    def test_boot_requires_selected_machine_login(self):
        machine = 'numaker-iot-nuc980g2'
        text = f'U-Boot Linux version {machine} login:'
        self.assertTrue(deploy.boot_complete(text, machine))
        bad_text = 'U-Boot Linux version other-machine login:'
        self.assertFalse(deploy.boot_complete(bad_text, machine))

    def test_unsupported_machine_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported NUC980 machine'):
            deploy.discover_cases(deploy.REPO_ROOT, 'numaker-iot-ma35d03f80')


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for media in ('sd', 'spinand'):
            (self.root / f'nuwriter_program_{media}.bat').write_text('@echo off\n', encoding='ascii')
            (self.root / f'nuwriter-pack-{media}-numaker-iot-nuc980g2.bin').write_bytes(b'image')
        (self.root / 'install_nuwriter.bat').write_text('@echo off\n', encoding='ascii')

    def test_discovers_two_cases_and_excludes_installer(self):
        cases = deploy.discover_cases(self.root)
        self.assertEqual([case.media for case in cases], ['sd', 'spinand'])
        self.assertEqual([case.deploy_option for case in cases], [7, 4])

    def test_missing_image_fails_discovery(self):
        (self.root / 'nuwriter-pack-sd-numaker-iot-nuc980g2.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing regular image'):
            deploy.discover_cases(self.root)

    def test_sd_uses_wic_when_no_sd_pack_exists(self):
        (self.root / 'nuwriter-pack-sd-numaker-iot-nuc980g2.bin').unlink()
        image = self.root / 'obmc-phosphor-image-numaker-iot-nuc980g2-20261104.wic'
        image.write_bytes(b'disk image')
        cases = deploy.discover_cases(self.root)
        self.assertEqual(next(case.image for case in cases if case.media == 'sd'), image)

    def test_sd_prefers_canonical_wic_when_pack_missing(self):
        (self.root / 'nuwriter-pack-sd-numaker-iot-nuc980g2.bin').unlink()
        image = self.root / 'obmc-phosphor-image-numaker-iot-nuc980g2.wic'
        image.write_bytes(b'disk image')
        (self.root / 'obmc-phosphor-image-numaker-iot-nuc980g2-20261104.wic').write_bytes(b'versioned image')
        cases = deploy.discover_cases(self.root)
        self.assertEqual(next(case.image for case in cases if case.media == 'sd'), image)

    def test_ambiguous_sd_wic_images_are_rejected(self):
        (self.root / 'nuwriter-pack-sd-numaker-iot-nuc980g2.bin').unlink()
        for version in ('20261103', '20261104'):
            (self.root / f'obmc-phosphor-image-numaker-iot-nuc980g2-{version}.wic').write_bytes(b'disk image')
        with self.assertRaisesRegex(ValueError, 'Ambiguous SD WIC images'):
            deploy.discover_cases(self.root)

    def test_sd_rejects_wic_for_another_machine(self):
        (self.root / 'nuwriter-pack-sd-numaker-iot-nuc980g2.bin').unlink()
        (self.root / 'obmc-phosphor-image-numaker-iot-ma35d03f80.wic').write_bytes(b'disk image')
        with self.assertRaisesRegex(ValueError, 'Missing regular image'):
            deploy.discover_cases(self.root)

    def test_no_supported_batches_fails_discovery(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaisesRegex(ValueError, 'No supported nuwriter_program_\\*\\.bat files'):
                deploy.discover_cases(Path(empty_dir))

    def test_skips_installed_tool_directory(self):
        tool_dir = self.root / 'NUC980_PyNuWriter'
        tool_dir.mkdir()
        (tool_dir / 'nuwriter_program_sd.bat').touch()
        cases = deploy.discover_cases(self.root)
        self.assertEqual(len(cases), 2)

    def test_listing_produces_json_without_hardware(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = deploy.main(['deploy', '--list-only', '--prebuilt-root', str(self.root)])
        self.assertEqual(code, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['media'], 'sd')
        self.assertEqual(data[1]['media'], 'spinand')


class CommandPlanTests(unittest.TestCase):
    def test_bundled_download_hook_triggers_ch341_reset_for_each_medium(self):
        hook = deploy.DEFAULT_DOWNLOAD_HOOK
        case = deploy.DeploymentCase('test', 'spinand', Path('test.bat'), Path('pack.bin'), 4)
        cmd = deploy.download_command(hook, case, '/dev/ttyACM0')
        self.assertEqual(cmd, [sys.executable, str(hook), '--media', 'spinand', '--deploy-option', '4',
                               '--serial-port', '/dev/ttyACM0'])

    def test_bundled_boot_hook_triggers_ch341_reset(self):
        hook = deploy.DEFAULT_BOOT_HOOK
        case = deploy.DeploymentCase('test', 'spinand', Path('test.bat'), Path('pack.bin'), 4)
        cmd = deploy.boot_command(hook, case, '/dev/ttyACM0')
        self.assertEqual(cmd, [sys.executable, str(hook), '4', '--media', 'spinand', '--deploy-option', '4',
                               '--serial-port', '/dev/ttyACM0'])

    def test_native_boot_commands_match_dram_execution(self):
        root = deploy.DEFAULT_NUWRITER_ROOT
        case = deploy.DeploymentCase('test', 'spinand', Path('test.bat'), Path('pack.bin'), 4)
        uboot = Path('/path/to/u-boot.bin')
        cmds = deploy.native_boot_commands(root, case, uboot)
        self.assertEqual(cmds[0], [sys.executable, str(root / 'nuwriter.py'), '-a', 'NUC980DK71YC.ini',
                                   '-w', 'ddr', '0x00e00000', str(uboot), '-o', 'execute'])

        spl = Path('/path/to/u-boot-spl.bin')
        cmds_spl = deploy.native_boot_commands(root, case, spl)
        self.assertEqual(cmds_spl[0], [sys.executable, str(root / 'nuwriter.py'), '-a', 'NUC980DK71YC.ini',
                                       '-w', 'ddr', '0x200', str(spl), '-o', 'execute'])

    def test_discover_boot_image_selects_media_specific_uboot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            machine = 'numaker-iot-nuc980g2'
            (root / f'u-boot-sd-{machine}.bin').write_bytes(b'sd')
            (root / f'u-boot-spinand-{machine}.bin').write_bytes(b'spinand')
            (root / f'u-boot-spl-{machine}.bin').write_bytes(b'spl')
            sd_case = deploy.DeploymentCase('case_sd', 'sd', root / 'sd.bat', root / 'pack.bin', 7, machine)
            spinand_case = deploy.DeploymentCase('case_spinand', 'spinand', root / 'spinand.bat', root / 'pack.bin', 4, machine)
            self.assertEqual(deploy.discover_boot_image(sd_case).name, f'u-boot-sd-{machine}.bin')
            self.assertEqual(deploy.discover_boot_image(spinand_case).name, f'u-boot-spl-{machine}.bin')

    def test_discover_boot_image_spinand_falls_back_without_spl(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            machine = 'numaker-iot-nuc980g2'
            (root / f'u-boot-spinand-{machine}.bin').write_bytes(b'spinand')
            spinand_case = deploy.DeploymentCase('case_spinand', 'spinand', root / 'spinand.bat', root / 'pack.bin', 4, machine)
            self.assertEqual(deploy.discover_boot_image(spinand_case).name, f'u-boot-spinand-{machine}.bin')

    def test_discover_boot_image_rejects_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = deploy.DeploymentCase('case', 'sd', root / 'sd.bat', root / 'pack.bin', 7)
            with self.assertRaisesRegex(ValueError, 'Missing regular U-Boot boot image'):
                deploy.discover_boot_image(case)

    def test_raw_sd_wic_is_written_at_offset_zero(self):
        root = deploy.DEFAULT_NUWRITER_ROOT
        case = deploy.DeploymentCase('test', 'sd', Path('test.bat'), Path('image.wic'), 7)
        cmds = deploy.flash_commands(root, case)
        self.assertEqual(cmds[-1], [sys.executable, str(root / 'nuwriter.py'), '-w', 'sd', '0x0', str(Path('image.wic'))])

    def test_python_hook_uses_current_interpreter_on_all_platforms(self):
        hook = Path(__file__).resolve()
        cmd = deploy.script_command(hook, ['arg1', 'arg2'])
        self.assertEqual(cmd, [sys.executable, str(hook), 'arg1', 'arg2'])

    def test_windows_batch_is_rejected_on_other_platforms(self):
        batch = deploy.DEFAULT_NUWRITER_ROOT / 'test.bat'
        batch.touch()
        self.addCleanup(batch.unlink)
        with self.assertRaises(ValueError):
            deploy.script_command(batch, [], platform='linux')

    def test_windows_batch_paths_with_spaces_are_quoted(self):
        batch = deploy.DEFAULT_NUWRITER_ROOT / 'test space.bat'
        batch.touch()
        self.addCleanup(batch.unlink)
        cmd = deploy.script_command(batch, ['arg1'], platform='win32')
        self.assertIn(f'"{batch}"', cmd[-1])

    def test_unsafe_shell_characters_in_batch_arguments_are_rejected(self):
        batch = deploy.DEFAULT_NUWRITER_ROOT / 'test.bat'
        batch.touch()
        self.addCleanup(batch.unlink)
        with self.assertRaisesRegex(ValueError, 'Unsafe shell characters'):
            deploy.script_command(batch, ['arg&evil'], platform='win32')

    def test_post_boot_test_commands_select_redfish_script(self):
        with tempfile.TemporaryDirectory() as temporary:
            doc_root = Path(temporary)
            machine = 'numaker-iot-nuc980g2'
            machine_dir = doc_root / machine
            machine_dir.mkdir(parents=True)
            redfish_script = machine_dir / 'test-redfish.sh'
            redfish_script.write_text('#!/bin/bash\n', encoding='ascii')
            case = deploy.DeploymentCase('test', 'spinand', Path('test.bat'), Path('pack.bin'), 4, machine)
            tests = deploy.post_boot_test_commands(case, 'bmc.local', doc_root=doc_root)
            self.assertEqual(len(tests), 1)
            self.assertEqual(tests[0][0], 'test-01-redfish')
            self.assertEqual(tests[0][1], ['/bin/bash', str(redfish_script), 'bmc.local'])


class BootValidationTests(unittest.TestCase):
    def test_wait_for_boot_uses_selected_machine(self):
        mock_console = mock.Mock()
        mock_console.in_waiting = 0
        mock_console.read.return_value = b''
        capture = deploy.SerialCapture(mock_console, Path(tempfile.mktemp()), machine='numaker-iot-nuc980g2', echo=False)
        capture.data.extend(b'U-Boot ... Linux version ... numaker-iot-nuc980g2 login:')
        deploy.wait_for_boot(capture, time.monotonic() + 5.0, observe_seconds=0.01)

    def test_wait_for_boot_rejects_another_machine_login(self):
        mock_console = mock.Mock()
        mock_console.in_waiting = 0
        mock_console.read.return_value = b''
        capture = deploy.SerialCapture(mock_console, Path(tempfile.mktemp()), machine='numaker-iot-nuc980g2', echo=False)
        capture.data.extend(b'U-Boot ... Linux version ... other-machine login:')
        with self.assertRaises(TimeoutError):
            deploy.wait_for_boot(capture, time.monotonic() + 0.05, observe_seconds=0.01)

    def test_complete_ordered_boot(self):
        text = 'U-Boot 2026.01 ... Linux version 6.6 ... numaker-iot-nuc980g2 login:'
        self.assertTrue(deploy.boot_complete(text, 'numaker-iot-nuc980g2'))

    def test_incomplete_or_stale_log_is_not_a_pass(self):
        self.assertFalse(deploy.boot_complete('U-Boot only', 'numaker-iot-nuc980g2'))
        self.assertFalse(deploy.boot_complete('numaker-iot-nuc980g2 login:', 'numaker-iot-nuc980g2'))

    def test_failures_override_success(self):
        for pattern in ('Kernel panic - not syncing', '\nASSERT: failed', '\nNUC980>\n', '\n=>\n'):
            with self.subTest(pattern=pattern):
                text = f'U-Boot Linux version {pattern} numaker-iot-nuc980g2 login:'
                with self.assertRaises(RuntimeError):
                    deploy.boot_complete(text, 'numaker-iot-nuc980g2')

    def test_serial_capture_handles_markers_split_across_reads(self):
        mock_console = mock.Mock()
        mock_console.in_waiting = 1
        chunks = [b'U-Boot\n', b'Linux version\n', b'numaker-iot-nuc980g2 log', b'in:\n']
        mock_console.read.side_effect = chunks
        capture = deploy.SerialCapture(mock_console, Path(tempfile.mktemp()), machine='numaker-iot-nuc980g2', echo=False)
        for _ in chunks:
            capture.drain()
        self.assertTrue(deploy.boot_complete(capture.text, 'numaker-iot-nuc980g2'))


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        machine = 'numaker-iot-nuc980g2'
        for media in ('sd', 'spinand'):
            (self.root / f'nuwriter_program_{media}.bat').write_text('@echo off\n', encoding='ascii')
            (self.root / f'nuwriter-pack-{media}-{machine}.bin').write_bytes(b'image')
        (self.root / f'u-boot-sd-{machine}.bin').write_bytes(b'uboot-sd')
        (self.root / f'u-boot-spinand-{machine}.bin').write_bytes(b'uboot-spinand')
        self.args = deploy.build_parser().parse_args([
            'deploy', '--prebuilt-root', str(self.root),
            '--output-directory', str(self.root / 'reports'),
            '--serial-port', 'fixture-uart',
        ])

    def test_all_cases_capture_fresh_uart_and_pass(self):
        console = mock.Mock(in_waiting=0)
        with mock.patch.object(deploy, 'validate_configuration'), \
                mock.patch.object(deploy, 'run_process'), \
                mock.patch.object(deploy, 'device_count', return_value=1), \
                mock.patch.object(deploy, 'open_console', return_value=console), \
                mock.patch.object(deploy, 'wait_for_boot'):
            code = deploy.deploy_cases(self.args)
        self.assertEqual(code, 0)
        self.assertEqual(console.reset_input_buffer.call_count, 2)
        self.assertEqual(console.close.call_count, 2)
        results = json.loads((self.root / 'reports/results.json').read_text())
        self.assertEqual([result['status'] for result in results], ['passed', 'passed'])

    def test_two_devices_block_every_flash(self):
        with mock.patch.object(deploy, 'validate_configuration'), \
                mock.patch.object(deploy, 'run_process'), \
                mock.patch.object(deploy, 'device_count', return_value=2), \
                mock.patch.object(deploy, 'open_console'):
            code = deploy.deploy_cases(self.args)
        self.assertEqual(code, 1)
        results = json.loads((self.root / 'reports/results.json').read_text())
        self.assertEqual([result['status'] for result in results], ['failed', 'failed'])
        self.assertIn('Expected exactly one NuWriter DUT; detected 2', results[0]['error'])

    def test_flash_failures_do_not_skip_subsequent_cases(self):
        console = mock.Mock(in_waiting=0)
        def run_proc(cmd, cwd, log_prefix, *args, **kwargs):
            if 'flash' in log_prefix.name:
                raise RuntimeError('Simulated flash error')
            return ''
        with mock.patch.object(deploy, 'validate_configuration'), \
                mock.patch.object(deploy, 'run_process', side_effect=run_proc), \
                mock.patch.object(deploy, 'device_count', return_value=1), \
                mock.patch.object(deploy, 'open_console', return_value=console):
            code = deploy.deploy_cases(self.args)
        self.assertEqual(code, 1)
        results = json.loads((self.root / 'reports/results.json').read_text())
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['status'], 'failed')
        self.assertEqual(results[1]['status'], 'failed')

    def test_colored_storage_and_phase_banners_in_output(self):
        console = mock.Mock(in_waiting=0)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), \
                mock.patch.object(deploy, 'validate_configuration'), \
                mock.patch.object(deploy, 'run_process'), \
                mock.patch.object(deploy, 'device_count', return_value=1), \
                mock.patch.object(deploy, 'open_console', return_value=console), \
                mock.patch.object(deploy, 'wait_for_boot'):
            deploy.deploy_cases(self.args)
        output = stdout.getvalue()
        self.assertIn('[STORAGE: SD]', output)
        self.assertIn('[STORAGE: SPINAND]', output)
        self.assertIn('[PHASE: DOWNLOAD-MODE]', output)
        self.assertIn('[PHASE: FLASH]', output)
        self.assertIn('[PHASE: BOOT]', output)
        self.assertIn('[PHASE: COMPLETE]', output)

    def test_nonzero_process_exit_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            prefix = Path(temporary) / 'step'
            with self.assertRaises(RuntimeError):
                deploy.run_process([sys.executable, '-c', 'import sys; sys.exit(42)'],
                                   Path(temporary), prefix, 5.0, echo=False)

    def test_process_timeout_terminates_without_hardware(self):
        with tempfile.TemporaryDirectory() as temporary:
            prefix = Path(temporary) / 'step'
            with self.assertRaises(TimeoutError):
                deploy.run_process([sys.executable, '-c', 'import time; time.sleep(10)'],
                                   Path(temporary), prefix, 0.1, echo=False)

    def test_reports_keep_json_array_and_escape_junit(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            results = [{'name': 'case1', 'media': 'sd', 'seconds': 12.3, 'status': 'passed', 'error': ''},
                       {'name': 'case2', 'media': 'spinand', 'seconds': 4.5, 'status': 'failed', 'error': 'err<>&"'}]
            deploy.write_results(results, out)
            data = json.loads((out / 'results.json').read_text(encoding='utf-8'))
            self.assertEqual(len(data), 2)
            junit = (out / 'junit.xml').read_text(encoding='utf-8')
            self.assertIn('failures="1"', junit)
            self.assertIn('err&lt;&gt;&amp;"', junit)


class SourceResolutionTests(unittest.TestCase):
    def test_local_source_never_calls_github(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'my-prebuilt'
            root.mkdir()
            ws = Path(temporary) / 'ws'
            ws.mkdir()
            env = {'SOURCE_MODE': 'local', 'NUC980_PREBUILT_ROOT': str(root)}
            mock_req = mock.Mock()
            values = deploy.resolve_source(ws, environment=env, request_json=mock_req)
            self.assertEqual(values['prebuilt_root'], str(root))
            mock_req.assert_not_called()

    def test_approved_artifact_writes_outputs_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            ws = Path(temporary) / 'ws'
            ws.mkdir()
            env = {'SOURCE_MODE': 'artifact', 'SOURCE_RUN_ID': '12345'}
            workflow_data = {'id': 99}
            run_data = {
                'id': 12345, 'workflow_id': 99, 'status': 'completed',
                'conclusion': 'success', 'head_branch': 'numaker',
                'head_repository': {'full_name': 'OpenNuvoton/openbmc'},
                'event': 'push', 'head_sha': 'feedbeef',
            }
            artifacts_data = {
                'artifacts': [{'id': 888, 'name': 'openbmc-numaker-iot-nuc980g2', 'expired': False}]
            }
            def mock_req(url, token):
                if '/workflows/' in url:
                    return workflow_data
                if '/runs/12345/artifacts' in url:
                    return artifacts_data
                if '/runs/12345' in url:
                    return run_data
                raise ValueError(f'Unexpected URL: {url}')

            values = deploy.resolve_source(ws, environment=env, request_json=mock_req)
            self.assertEqual(values['run_id'], '12345')
            self.assertEqual(values['artifact_id'], '888')

    def test_github_output_rejects_newline_injection(self):
        with self.assertRaises(ValueError):
            deploy.append_github_outputs('some_path', {'key': 'evil\nvalue'})

    def test_summary_reads_python_result_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            results = [{'name': 'case1', 'media': 'sd', 'status': 'passed', 'phase': 'complete', 'seconds': 1.2}]
            (out / 'results.json').write_text(json.dumps(results), encoding='utf-8')
            summary = deploy.publish_summary(out, None)
            self.assertIn('## NUC980 deployment and boot tests', summary)
            self.assertIn('| case1 | sd | passed | complete | 1.2 |', summary)


class RunnerConfigurationTests(unittest.TestCase):
    def test_all_machines_validate_with_ddr_ini(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            machine = 'numaker-iot-nuc980g2'
            (root / 'nuwriter_program_sd.bat').touch()
            (root / f'nuwriter-pack-sd-{machine}.bin').touch()
            (root / f'u-boot-sd-{machine}.bin').write_bytes(b'uboot-sd')
            args = deploy.build_parser().parse_args([
                'check-runner', '--prebuilt-root', str(root), '--serial-port', 'fixture-uart'
            ])
            with mock.patch.object(deploy, 'check_dependencies'), \
                    mock.patch.object(deploy, 'available_serial_ports', return_value=['fixture-uart']):
                deploy.validate_configuration(args)

    def test_missing_uboot_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            machine = 'numaker-iot-nuc980g2'
            (root / 'nuwriter_program_sd.bat').touch()
            (root / f'nuwriter-pack-sd-{machine}.bin').touch()
            args = deploy.build_parser().parse_args([
                'check-runner', '--prebuilt-root', str(root), '--serial-port', 'fixture-uart'
            ])
            with mock.patch.object(deploy, 'check_dependencies'), \
                    mock.patch.object(deploy, 'available_serial_ports', return_value=['fixture-uart']), \
                    self.assertRaisesRegex(ValueError, 'Missing regular U-Boot boot image'):
                deploy.validate_configuration(args)

    def test_missing_download_hook_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = deploy.build_parser().parse_args([
                'check-runner', '--prebuilt-root', str(root), '--serial-port', 'fixture-uart',
                '--download-hook', str(root / 'missing_download.py')
            ])
            with mock.patch.object(deploy, 'check_dependencies'), \
                    mock.patch.object(deploy, 'available_serial_ports', return_value=['fixture-uart']), \
                    self.assertRaises(ValueError):
                deploy.validate_configuration(args)

    def test_unavailable_uart_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = deploy.build_parser().parse_args([
                'check-runner', '--prebuilt-root', str(root), '--serial-port', 'nonexistent-uart'
            ])
            with mock.patch.object(deploy, 'check_dependencies'), \
                    mock.patch.object(deploy, 'available_serial_ports', return_value=['other-uart']), \
                    self.assertRaisesRegex(ValueError, 'Unavailable DUT UART port'):
                deploy.validate_configuration(args)

    def test_cli_rejects_out_of_range_timeouts(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            deploy.build_parser().parse_args(['deploy', '--flash-timeout-seconds', '10'])

    def test_cli_accepts_float_formatted_integer_numbers_from_github_actions(self):
        args = deploy.build_parser().parse_args(['deploy', '--flash-timeout-seconds', '1800.0'])
        self.assertEqual(args.flash_timeout_seconds, 1800)


if __name__ == '__main__':
    unittest.main()
