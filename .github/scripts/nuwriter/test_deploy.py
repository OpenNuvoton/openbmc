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
            self.assertEqual(deploy.prebuilt_directory(args), root / 'artifacts/openbmc-numaker-iot-ma35d03f80')
            self.assertEqual(args.output_directory, root / 'autodeploy-results')
            self.assertEqual(args.nuwriter_root, Path(deploy.__file__).resolve().parent)
        self.assertEqual(deploy.build_parser().parse_args(['resolve-source']).workspace, root)
        self.assertEqual(deploy.build_parser().parse_args(['summary']).output_directory, root / 'autodeploy-results')

    def test_environment_paths_are_converted_to_paths(self):
        with mock.patch.dict(os.environ, {'MA35_NUWRITER_ROOT': 'external NuWriter',
                                          'MA35_PREBUILT_ROOT': 'local images'}):
            args = deploy.build_parser().parse_args(['deploy'])
        self.assertEqual(args.nuwriter_root, Path('external NuWriter'))
        self.assertEqual(args.prebuilt_root, Path('local images'))

    def test_cli_paths_override_environment(self):
        with mock.patch.dict(os.environ, {'MA35_NUWRITER_ROOT': 'environment-tools',
                                          'MA35_PREBUILT_ROOT': 'environment-images'}):
            args = deploy.build_parser().parse_args([
                'deploy', '--nuwriter-root', 'cli-tools', '--prebuilt-root', 'cli-images'])
        self.assertEqual(args.nuwriter_root, Path('cli-tools'))
        self.assertEqual(args.prebuilt_root, Path('cli-images'))

    def test_default_runtime_reaches_hook_validation_without_hardware(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error), mock.patch.object(deploy, 'check_dependencies') as dependencies, \
                mock.patch.object(deploy, 'run_process') as process:
            self.assertEqual(deploy.main(['check-runner']), 1)
        self.assertIn('MA35_DOWNLOAD_HOOK or --download-hook', error.getvalue())
        dependencies.assert_called_once()
        process.assert_not_called()

    def test_defaults_do_not_depend_on_current_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(Path, 'cwd', return_value=Path(temporary)):
            args = deploy.build_parser().parse_args(['deploy'])
        self.assertEqual(deploy.prebuilt_directory(args), deploy.DEFAULT_PREBUILT_ROOT)
        self.assertEqual(args.output_directory, deploy.DEFAULT_OUTPUT_DIRECTORY)
        self.assertEqual(args.nuwriter_root, Path(deploy.__file__).resolve().parent)

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

    def test_cli_machine_overrides_environment_and_preserves_explicit_directory(self):
        with mock.patch.dict(os.environ, {'MA35_MACHINE': 'numaker-iot-ma35d03f80'}):
            args = deploy.build_parser().parse_args([
                'deploy', '--machine', 'numaker-iot-ma35d16fj87c', '--prebuilt-root', 'custom-images'])
        self.assertEqual(args.machine, 'numaker-iot-ma35d16fj87c')
        self.assertEqual(deploy.prebuilt_directory(args), Path('custom-images'))

    def test_environment_selects_machine_for_all_commands(self):
        with mock.patch.dict(os.environ, {'MA35_MACHINE': 'numaker-iot-ma35d05ki1'}):
            for command in ('deploy', 'check-runner', 'resolve-source'):
                self.assertEqual(deploy.build_parser().parse_args([command]).machine, 'numaker-iot-ma35d05ki1')

    def test_unsupported_cli_and_environment_machines_are_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            deploy.build_parser().parse_args(['deploy', '--machine', 'numaker-iot-nuc980g2'])
        with mock.patch.dict(os.environ, {'MA35_MACHINE': 'numaker-iot-nuc980g2'}), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            deploy.build_parser().parse_args(['deploy'])

    def test_supported_machines_share_auto_ddr_image(self):
        self.assertEqual(deploy.SUPPORTED_MACHINES, (
            'numaker-iot-ma35d03f80', 'numaker-iot-ma35d05ki1', 'numaker-iot-ma35d16fj87c'))
        self.assertEqual(deploy.DDR_IMAGE, 'ddrimg/ddr_auto.bin')
        self.assertTrue((deploy.DEFAULT_NUWRITER_ROOT / deploy.DDR_IMAGE).is_file())

    def test_discovery_selects_each_machine_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'nuwriter_program_sd.bat').touch()
            for machine in deploy.SUPPORTED_MACHINES:
                image = root / f'nuwriter-pack-sd-{machine}.bin'
                image.write_bytes(b'fixture')
            for machine in deploy.SUPPORTED_MACHINES:
                with self.subTest(machine=machine):
                    cases = deploy.discover_cases(root, machine)
                    self.assertEqual(len(cases), 1)
                    self.assertEqual(cases[0].image.name, f'nuwriter-pack-sd-{machine}.bin')
                    self.assertEqual(cases[0].to_dict()['machine'], machine)

    def test_wrong_machine_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'nuwriter_program_sd.bat').touch()
            (root / 'nuwriter-pack-sd-numaker-iot-ma35d03f80.bin').write_bytes(b'fixture')
            with self.assertRaisesRegex(ValueError, 'Missing regular image'):
                deploy.discover_cases(root, 'numaker-iot-ma35d05ki1')

    def test_flash_and_native_boot_use_auto_ddr_for_all_machines(self):
        root = deploy.DEFAULT_NUWRITER_ROOT
        for machine in deploy.SUPPORTED_MACHINES:
            with self.subTest(machine=machine):
                case = deploy.DeploymentCase('case', 'sd', root / 'case.bat', root / 'pack.bin', 7, machine)
                for commands in (deploy.flash_commands(root, case),
                                 deploy.native_boot_commands(root, case, root / 'bl2.dtb', root / 'bl2.bin')):
                    self.assertEqual(commands[0], [sys.executable, str(root / 'nuwriter.py'), '-a', 'ddrimg/ddr_auto.bin'])

    def test_boot_requires_selected_machine_login(self):
        for machine in deploy.SUPPORTED_MACHINES:
            for logged_in_machine in deploy.SUPPORTED_MACHINES:
                with self.subTest(machine=machine, logged_in_machine=logged_in_machine):
                    text = f'BL2: U-Boot Linux version {logged_in_machine} login:'
                    self.assertEqual(deploy.boot_complete(text, machine), machine == logged_in_machine)

    def test_unsupported_machine_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported MA35 machine'):
            deploy.discover_cases(deploy.REPO_ROOT, 'numaker-iot-nuc980g2')


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for media in ('nand', 'sd', 'spinand'):
            (self.root / f'nuwriter_program_{media}.bat').write_text('@echo off\n', encoding='ascii')
            (self.root / f'nuwriter-pack-{media}-numaker-iot-ma35d03f80.bin').write_bytes(b'image')
        (self.root / 'install_nuwriter.bat').write_text('@echo off\n', encoding='ascii')

    def test_discovers_three_cases_and_excludes_installer(self):
        cases = deploy.discover_cases(self.root)
        self.assertEqual([case.media for case in cases], ['nand', 'sd', 'spinand'])
        self.assertEqual([case.deploy_option for case in cases], [5, 7, 3])

    def test_missing_image_fails_discovery(self):
        (self.root / 'nuwriter-pack-sd-numaker-iot-ma35d03f80.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing regular image'):
            deploy.discover_cases(self.root)

    def test_no_supported_batches_fails_discovery(self):
        for script in self.root.glob('nuwriter_program_*.bat'):
            script.unlink()
        with self.assertRaisesRegex(ValueError, 'No supported'):
            deploy.discover_cases(self.root)

    def test_skips_installed_tool_directory(self):
        tools = self.root / 'MA35D1_NuWriter'
        tools.mkdir()
        (tools / 'nuwriter_program_sd.bat').write_text('@echo off\n', encoding='ascii')
        self.assertEqual(len(deploy.discover_cases(self.root)), 3)

    def test_skips_a_symbolic_directory_cycle(self):
        link = self.root / 'cycle'
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symlinks is not permitted by this OS account')
        self.addCleanup(link.unlink)
        self.assertEqual(len(deploy.discover_cases(self.root)), 3)

    def test_nested_directories_with_spaces(self):
        nested = self.root / 'image with spaces'
        nested.mkdir()
        for path in self.root.glob('*sd*'):
            path.rename(nested / path.name)
        self.assertEqual(len(deploy.discover_cases(self.root)), 3)

    def test_listing_produces_json_without_hardware(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), mock.patch.object(deploy, 'validate_configuration') as validate:
            self.assertEqual(deploy.main(['--prebuilt-root', str(self.root), '--list-only']), 0)
        validate.assert_not_called()
        self.assertEqual(len(json.loads(output.getvalue())), 3)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ma35 path with spaces ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.case = deploy.DeploymentCase('nuwriter_program_sd', 'sd', self.root / 'case.bat', self.root / 'pack.bin', 7)

    def test_native_commands_match_prebuilt_batches(self):
        for media in ('nand', 'sd', 'spinand'):
            case = deploy.DeploymentCase('case', media, self.case.script, self.case.image, deploy.DEPLOY_OPTIONS[media])
            commands = deploy.flash_commands(self.root, case)
            self.assertEqual(commands[0], [sys.executable, str(self.root / 'nuwriter.py'), '-a', 'ddrimg/ddr_auto.bin'])
            self.assertEqual(commands[-1][2:], ['-w', 'emmc' if media == 'sd' else media, str(case.image)])
            self.assertEqual(len(commands), 2 if media == 'sd' else 3)
            if media != 'sd':
                self.assertEqual(commands[1][2:], ['-e', media, 'all'])

    def test_python_hook_uses_current_interpreter_on_all_platforms(self):
        path = self.root / 'reset.py'
        path.touch()
        for platform in ('win32', 'linux', 'darwin'):
            self.assertEqual(deploy.script_command(path, ['7'], platform), [sys.executable, str(path.resolve()), '7'])

    def test_windows_batch_is_rejected_on_other_platforms(self):
        path = self.root / 'boot.bat'
        path.touch()
        for platform in ('linux', 'darwin'):
            with self.assertRaisesRegex(ValueError, 'Windows batch cannot run'):
                deploy.script_command(path, ['7'], platform)

    def test_windows_batch_paths_with_spaces_are_quoted(self):
        path = self.root / 'boot.bat'
        path.touch()
        command = deploy.script_command(path, ['7'], 'win32')
        self.assertEqual(command[1:5], ['/d', '/v:off', '/s', '/c'])
        self.assertEqual(command[-1], f'""{path.resolve()}" "7""')

    def test_unsafe_shell_characters_in_batch_arguments_are_rejected(self):
        path = self.root / 'boot.bat'
        path.touch()
        with self.assertRaisesRegex(ValueError, 'Unsafe shell'):
            deploy.script_command(path, ['7 & echo bad'], 'win32')

    def test_posix_shell_hook_does_not_depend_on_powershell(self):
        path = self.root / 'reset.sh'
        path.touch()
        self.assertEqual(deploy.script_command(path, ['7'], 'linux'), ['/bin/sh', str(path.resolve()), '7'])
        with self.assertRaises(ValueError):
            deploy.script_command(path, ['7'], 'win32')

    def test_powershell_download_hook_preserves_legacy_parameter_names(self):
        path = self.root / 'reset.ps1'
        path.touch()
        with mock.patch.object(deploy.shutil, 'which', return_value='pwsh'):
            command = deploy.download_command(path, self.case, 'COM3')
        self.assertEqual(command[-6:], ['-Media', 'sd', '-DeployOption', '7', '-SerialPort', 'COM3'])

    def test_native_boot_writes_selector_then_dtb_and_executes_bl2_last(self):
        commands = deploy.native_boot_commands(self.root, self.case, self.root / 'bl2.dtb', self.root / 'bl2.bin')
        self.assertEqual(commands[1][2:], ['-w', 'reg', '0x2803FFFC', '0x00004400'])
        self.assertEqual(commands[-2][2:5], ['-w', 'sram', '0x28023000'])
        self.assertEqual(commands[-1][-2:], ['-o', 'execute'])


class BootTests(unittest.TestCase):
    def test_wait_for_boot_uses_selected_machine(self):
        for machine in deploy.SUPPORTED_MACHINES:
            with self.subTest(machine=machine):
                capture = mock.Mock(text=f'BL2: U-Boot Linux version {machine} login:')
                with mock.patch.object(deploy.time, 'monotonic', return_value=0):
                    deploy.wait_for_boot(capture, deadline=10, observe_seconds=0, machine=machine)
                capture.drain.assert_called_once_with(block=True)

    def test_wait_for_boot_rejects_another_machine_login(self):
        capture = mock.Mock(text='BL2: U-Boot Linux version numaker-iot-ma35d03f80 login:')
        with mock.patch.object(deploy.time, 'monotonic', side_effect=[0, 11]):
            with self.assertRaises(TimeoutError):
                deploy.wait_for_boot(capture, deadline=10, observe_seconds=0, machine='numaker-iot-ma35d05ki1')

    def test_complete_ordered_boot(self):
        self.assertTrue(deploy.boot_complete('BL2: release U-Boot Linux version 6.6 numaker-iot-ma35d03f80 login:'))

    def test_incomplete_or_stale_log_is_not_a_pass(self):
        for text in ('numaker-iot-ma35d03f80 login:', 'Successfully programmed 1 device(s)',
                     'Linux version BL2: U-Boot numaker-iot-ma35d03f80 login:'):
            self.assertFalse(deploy.boot_complete(text))

    def test_failures_override_success(self):
        for failure in ('Kernel panic - not syncing', 'Synchronous Abort', '\nASSERT: drivers/io/io_storage.c:179',
                        'ERROR: Boot interface 0x4f00 not supported'):
            with self.assertRaisesRegex(RuntimeError, 'Boot failure'):
                deploy.boot_complete('BL2: U-Boot Linux version numaker-iot-ma35d03f80 login:\n' + failure)

    def test_serial_capture_handles_markers_split_across_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            console = mock.Mock()
            console.in_waiting = 256
            console.read.side_effect = [b'BL2: U-Boot Linux ver', b'sion numaker-iot-ma35d03f80 login:']
            path = Path(temporary) / 'uart.log'
            capture = deploy.SerialCapture(console, path)
            capture.drain()
            self.assertFalse(deploy.boot_complete(capture.text))
            capture.drain()
            self.assertTrue(deploy.boot_complete(capture.text))
            self.assertEqual(path.read_bytes(), bytes(capture.data))

    def test_boot_deadline_and_post_login_observation(self):
        capture = mock.Mock(text='BL2: U-Boot Linux version numaker-iot-ma35d03f80 login:')
        with mock.patch.object(deploy.time, 'monotonic', side_effect=[0, 0, 0, 1, 1, 2, 2]):
            deploy.wait_for_boot(capture, deadline=10, observe_seconds=2)
        self.assertEqual(capture.drain.call_count, 3)
        with mock.patch.object(deploy.time, 'monotonic', return_value=11):
            with self.assertRaises(TimeoutError):
                deploy.wait_for_boot(capture, deadline=10, observe_seconds=2)


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ma35 process with spaces ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_separate_logs_and_spaced_path_arguments(self):
        output = deploy.run_process([sys.executable, '-c', 'import sys; print(sys.argv[1]); print("diagnostic", file=sys.stderr)',
                                     str(self.root)], self.root, self.root / 'success', 10)
        self.assertEqual(output.strip(), str(self.root))
        self.assertEqual((self.root / 'success.stderr.log').read_text().strip(), 'diagnostic')

    def test_nonzero_process_exit_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'code 7'):
            deploy.run_process([sys.executable, '-c', 'raise SystemExit(7)'], self.root, self.root / 'failed', 10)

    def test_process_timeout_terminates_without_hardware(self):
        started = time.monotonic()
        with self.assertRaisesRegex(TimeoutError, 'timed out'):
            deploy.run_process([sys.executable, '-c', 'while True: pass'], self.root, self.root / 'timeout', 0.2)
        self.assertLess(time.monotonic() - started, 10)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows batch compatibility')
    def test_real_windows_boot_batch_receives_numeric_option(self):
        path = self.root / 'boot.bat'
        path.write_text('@echo off\necho %~1\nexit /b 0\n', encoding='ascii')
        output = deploy.run_process(deploy.script_command(path, ['7']), self.root, self.root / 'batch', 10)
        self.assertEqual(output.strip(), '7')

    def test_reports_keep_json_array_and_escape_junit(self):
        result = {'name': 'case', 'media': 'sd', 'status': 'failed', 'phase': 'boot',
                  'seconds': 1.25, 'error': 'ASSERT: a < b & device unavailable'}
        deploy.write_results([result], self.root)
        self.assertEqual(json.loads((self.root / 'results.json').read_text()), [result])
        suite = ET.parse(self.root / 'junit.xml').getroot()
        self.assertEqual(suite.get('failures'), '1')
        self.assertEqual(suite.find('testcase/failure').get('message'), result['error'])


class SequentialTests(unittest.TestCase):
    def setUp(self):
        DiscoveryTests.setUp(self)
        self.args = deploy.build_parser().parse_args(['deploy', '--prebuilt-root', str(self.root),
                                                     '--nuwriter-root', str(self.root),
                                                     '--output-directory', str(self.root / 'reports')])
        self.args.download_hook = self.root / 'reset.py'
        self.args.download_hook.touch()
        self.args.boot_script = self.root / 'boot.py'
        self.args.boot_script.touch()
        self.args.serial_port = 'fixture-uart'
        self.validation = mock.patch.object(deploy, 'validate_configuration')
        self.validation.start()
        self.addCleanup(self.validation.stop)

    def test_selected_machine_reaches_flash_uart_and_reports(self):
        for machine in deploy.SUPPORTED_MACHINES:
            with self.subTest(machine=machine):
                for media in deploy.DEPLOY_OPTIONS:
                    (self.root / f'nuwriter-pack-{media}-{machine}.bin').write_bytes(b'fixture')
                self.args.machine = machine
                console = mock.Mock(in_waiting=0)
                with mock.patch.object(deploy, 'run_process') as process, \
                        mock.patch.object(deploy, 'device_count', return_value=1), \
                        mock.patch.object(deploy, 'open_console', return_value=console), \
                        mock.patch.object(deploy, 'wait_for_boot') as wait:
                    self.assertEqual(deploy.deploy_cases(self.args), 0)
                initializations = [call.args[0] for call in process.call_args_list
                                   if call.args[2].name == 'flash-01']
                self.assertEqual(len(initializations), 3)
                self.assertTrue(all(command[-1] == 'ddrimg/ddr_auto.bin' for command in initializations))
                self.assertEqual(wait.call_count, 3)
                self.assertTrue(all(call.kwargs['machine'] == machine for call in wait.call_args_list))
                results = json.loads((self.root / 'reports/results.json').read_text())
                self.assertEqual([result['machine'] for result in results], [machine] * 3)
                self.assertEqual([result['status'] for result in results], ['passed'] * 3)

    def test_two_devices_block_every_flash(self):
        with mock.patch.object(deploy, 'run_process') as process, mock.patch.object(deploy, 'device_count', return_value=2):
            self.assertEqual(deploy.deploy_cases(self.args), 1)
        self.assertEqual(process.call_count, 3)
        self.assertTrue(all(call.args[2].name == 'reset' for call in process.call_args_list))
        results = json.loads((self.root / 'reports/results.json').read_text())
        self.assertEqual([result['phase'] for result in results], ['download-mode'] * 3)

    def test_flash_failures_do_not_skip_subsequent_cases(self):
        def process(command, cwd, log_prefix, timeout, capture=None):
            if log_prefix.name.startswith('flash-'):
                raise RuntimeError('Synthetic flash failure')
            return ''
        with mock.patch.object(deploy, 'run_process', side_effect=process), mock.patch.object(deploy, 'device_count', return_value=1):
            self.assertEqual(deploy.deploy_cases(self.args), 1)
        results = json.loads((self.root / 'reports/results.json').read_text())
        self.assertEqual(len(results), 3)
        self.assertEqual([result['phase'] for result in results], ['flash'] * 3)
        self.assertEqual([result['error'] for result in results], ['Synthetic flash failure'] * 3)

    def test_all_cases_capture_fresh_uart_and_pass(self):
        console = mock.Mock(in_waiting=0)
        with mock.patch.object(deploy, 'run_process'), mock.patch.object(deploy, 'device_count', return_value=1), \
                mock.patch.object(deploy, 'open_console', return_value=console), mock.patch.object(deploy, 'wait_for_boot'):
            self.assertEqual(deploy.deploy_cases(self.args), 0)
        self.assertEqual(console.reset_input_buffer.call_count, 3)
        self.assertEqual(console.close.call_count, 3)
        results = json.loads((self.root / 'reports/results.json').read_text())
        self.assertEqual([result['status'] for result in results], ['passed'] * 3)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ma35 source with spaces ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = {'SOURCE_MODE': 'artifact', 'SOURCE_RUN_ID': '101',
                            'GITHUB_OUTPUT': str(self.root / 'outputs.txt'), 'ARTIFACT_TOKEN': 'fixture-not-a-secret'}
        self.run = {'id': 101, 'workflow_id': 10, 'status': 'completed', 'conclusion': 'success',
                    'head_branch': 'master', 'head_repository': {'full_name': 'OpenNuvoton/openbmc'},
                    'event': 'workflow_dispatch', 'head_sha': 'a' * 40}
        self.artifact = {'id': 900, 'name': 'openbmc-numaker-iot-ma35d03f80', 'expired': False}
        self.artifacts = [self.artifact]
        self.request = mock.Mock(side_effect=self.request_json)

    def request_json(self, url, token):
        if url.endswith('/workflows/numaker.yml'):
            return {'id': 10}
        if url.endswith('/runs/101'):
            return self.run
        if '/workflows/numaker.yml/runs?' in url:
            return {'workflow_runs': [self.run]}
        if url.endswith('/runs/101/artifacts?per_page=100'):
            return {'artifacts': self.artifacts}
        raise AssertionError(f'Unexpected API request: {url}')

    def test_selects_one_machine_from_a_multi_machine_build(self):
        self.artifacts = [{'id': 900 + index, 'name': f'openbmc-{machine}', 'expired': False}
                          for index, machine in enumerate(deploy.SUPPORTED_MACHINES)]
        for machine, artifact in zip(deploy.SUPPORTED_MACHINES, self.artifacts):
            with self.subTest(machine=machine):
                self.environment['MA35_MACHINE'] = machine
                values = deploy.resolve_source(self.root, self.environment, self.request)
                self.assertEqual(values['artifact_id'], str(artifact['id']))
                self.assertEqual(values['prebuilt_root'], str(self.root / 'artifacts' / f'openbmc-{machine}'))
                self.assertEqual(json.loads((self.root / 'autodeploy-results/source.json').read_text())['machine'], machine)

    def test_unsupported_source_machine_fails_before_requesting_artifacts(self):
        self.environment['MA35_MACHINE'] = 'numaker-iot-nuc980g2'
        with self.assertRaisesRegex(ValueError, 'Unsupported MA35 machine'):
            deploy.resolve_source(self.root, self.environment, self.request)
        self.request.assert_not_called()

    def test_approved_artifact_writes_outputs_and_provenance(self):
        values = deploy.resolve_source(self.root, self.environment, self.request)
        self.assertEqual(values['run_id'], '101')
        self.assertEqual(values['artifact_id'], '900')
        self.assertIn('artifact_id=900', (self.root / 'outputs.txt').read_text(encoding='utf-8'))
        self.assertEqual(json.loads((self.root / 'autodeploy-results/source.json').read_text())['commit'], 'a' * 40)

    def test_rejects_untrusted_or_failed_runs(self):
        for key, value in (('head_branch', 'untrusted'), ('workflow_id', 11), ('event', 'pull_request'),
                           ('conclusion', 'failure'), ('head_repository', {'full_name': 'someone/openbmc'})):
            with self.subTest(key=key):
                original = self.run[key]
                self.run[key] = value
                with self.assertRaisesRegex(ValueError, 'not an approved'):
                    deploy.resolve_source(self.root, self.environment, self.request)
                self.run[key] = original

    def test_expired_artifact_is_not_accepted(self):
        self.artifact['expired'] = True
        with self.assertRaisesRegex(ValueError, 'non-expired'):
            deploy.resolve_source(self.root, self.environment, self.request)

    def test_invalid_run_id_fails_without_requesting_a_run(self):
        self.environment['SOURCE_RUN_ID'] = '101;invalid'
        with self.assertRaisesRegex(ValueError, 'positive integer'):
            deploy.resolve_source(self.root, self.environment, self.request)
        self.assertEqual(self.request.call_count, 1)

    def test_latest_successful_run_can_be_resolved(self):
        self.environment['SOURCE_RUN_ID'] = ''
        self.assertEqual(deploy.resolve_source(self.root, self.environment, self.request)['run_id'], '101')
        self.assertTrue(any('/runs?status=success&branch=master' in call.args[0] for call in self.request.call_args_list))

    def test_local_source_never_calls_github(self):
        self.environment.update(SOURCE_MODE='local', MA35_PREBUILT_ROOT=str(self.root))
        values = deploy.resolve_source(self.root, self.environment, self.request)
        self.assertEqual(values['prebuilt_root'], str(self.root.resolve()))
        self.request.assert_not_called()

    def test_github_output_rejects_newline_injection(self):
        with self.assertRaisesRegex(ValueError, 'newlines'):
            deploy.append_github_outputs(str(self.root / 'outputs.txt'), {'prebuilt_root': '/tmp/path\ninjected=true'})

    def test_summary_reads_python_result_schema(self):
        deploy.write_results([{'name': 'case', 'media': 'sd', 'status': 'passed', 'phase': 'complete',
                               'seconds': 1.0, 'error': ''}], self.root)
        destination = self.root / 'summary.md'
        summary = deploy.publish_summary(self.root, str(destination))
        self.assertIn('| case | sd | passed | complete | 1.0 |', summary)
        self.assertEqual(destination.read_text(), summary)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'ddrimg').mkdir()
        for filename in ('nuwriter.py', 'xusb.bin', 'ddrimg/ddr_auto.bin', 'reset.py', 'boot.py', 'bl2.bin', 'bl2.dtb'):
            (self.root / filename).write_bytes(b'fixture')
        self.args = deploy.build_parser().parse_args([
            'check-runner', '--nuwriter-root', str(self.root), '--serial-port', 'fixture-uart',
            '--download-hook', str(self.root / 'reset.py'), '--boot-script', str(self.root / 'boot.py')])
        dependencies = mock.patch.object(deploy, 'check_dependencies')
        ports = mock.patch.object(deploy, 'available_serial_ports', return_value=['fixture-uart'])
        self.dependencies = dependencies.start()
        ports.start()
        self.addCleanup(dependencies.stop)
        self.addCleanup(ports.stop)

    def test_all_machines_validate_with_only_auto_ddr(self):
        for machine in deploy.SUPPORTED_MACHINES:
            with self.subTest(machine=machine):
                self.args.machine = machine
                deploy.validate_configuration(self.args)

    def test_missing_auto_ddr_is_rejected(self):
        (self.root / 'ddrimg/ddr_auto.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'ddr_auto.bin'):
            deploy.validate_configuration(self.args)

    def test_existing_python_hooks_validate_without_hardware(self):
        with mock.patch.object(deploy, 'run_process') as process, mock.patch.object(deploy, 'open_console') as console:
            deploy.validate_configuration(self.args)
        process.assert_not_called()
        console.assert_not_called()
        self.dependencies.assert_called_once()

    def test_bundled_runtime_validates_without_a_runtime_argument(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(deploy, 'DEFAULT_NUWRITER_ROOT', self.root):
            args = deploy.build_parser().parse_args([
                'check-runner', '--serial-port', 'fixture-uart',
                '--download-hook', str(self.root / 'reset.py'), '--boot-script', str(self.root / 'boot.py')])
        with mock.patch.object(deploy, 'run_process') as process, mock.patch.object(deploy, 'open_console') as console:
            deploy.validate_configuration(args)
        self.assertEqual(args.nuwriter_root, self.root.resolve())
        self.assertEqual(deploy.nuwriter_command(args.nuwriter_root, '--help'),
                         [sys.executable, str(self.root.resolve() / 'nuwriter.py'), '--help'])
        process.assert_not_called()
        console.assert_not_called()

    def test_missing_download_hook_is_rejected(self):
        self.args.download_hook = None
        with self.assertRaisesRegex(ValueError, 'MA35_DOWNLOAD_HOOK'):
            deploy.validate_configuration(self.args)

    def test_unavailable_uart_is_rejected(self):
        self.args.serial_port = 'not-a-dut'
        with self.assertRaisesRegex(ValueError, 'Unavailable DUT UART'):
            deploy.validate_configuration(self.args)

    def test_missing_nuwriter_runtime_is_rejected(self):
        (self.root / 'xusb.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing NuWriter runtime'):
            deploy.validate_configuration(self.args)

    def test_native_boot_images_are_validated_without_external_boot_script(self):
        self.args.boot_script = None
        self.args.boot_dtb = str(self.root / 'bl2.dtb')
        self.args.boot_bl2 = str(self.root / 'bl2.bin')
        deploy.validate_configuration(self.args)
        self.assertEqual(self.args.boot_bl2, self.root / 'bl2.bin')

    def test_native_boot_images_are_discovered_in_nested_artifacts(self):
        images = self.root / 'artifacts' / 'numaker-iot-ma35d03f80'
        images.mkdir(parents=True)
        (self.root / 'bl2.dtb').rename(images / 'bl2-ma35d0.dtb')
        (self.root / 'bl2.bin').rename(images / 'bl2-ma35d0.bin')
        self.args.prebuilt_root = self.root / 'artifacts'
        self.args.boot_script = None
        self.args.boot_dtb = None
        self.args.boot_bl2 = None
        with mock.patch.object(deploy, 'run_process') as process, mock.patch.object(deploy, 'open_console') as console:
            deploy.validate_configuration(self.args)
        self.assertEqual(self.args.boot_dtb, images / 'bl2-ma35d0.dtb')
        self.assertEqual(self.args.boot_bl2, images / 'bl2-ma35d0.bin')
        process.assert_not_called()
        console.assert_not_called()

    def test_missing_artifact_boot_pair_is_rejected(self):
        (self.root / 'bl2.dtb').unlink()
        with self.assertRaisesRegex(ValueError, 'BL2/DTB pair.*found 0'):
            deploy.discover_boot_images(self.root)

    def test_artifact_dtb_requires_a_matching_bl2(self):
        (self.root / 'bl2.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing regular BL2 image paired'):
            deploy.discover_boot_images(self.root)

    def test_ambiguous_artifact_boot_pairs_are_rejected(self):
        images = self.root / 'another-build'
        images.mkdir()
        (images / 'bl2-ma35d0.dtb').write_bytes(b'fixture')
        (images / 'bl2-ma35d0.bin').write_bytes(b'fixture')
        with self.assertRaisesRegex(ValueError, 'BL2/DTB pair.*found 2'):
            deploy.discover_boot_images(self.root)

    def test_artifact_boot_images_retain_size_checks(self):
        self.args.prebuilt_root = self.root
        self.args.boot_script = None
        self.args.boot_dtb = None
        self.args.boot_bl2 = None
        (self.root / 'bl2.bin').write_bytes(b'\0' * 0x23001)
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            deploy.validate_configuration(self.args)

    def test_native_bl2_overlap_is_rejected(self):
        self.args.boot_script = None
        self.args.boot_dtb = str(self.root / 'bl2.dtb')
        self.args.boot_bl2 = str(self.root / 'bl2.bin')
        (self.root / 'bl2.bin').write_bytes(b'\0' * 0x23001)
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            deploy.validate_configuration(self.args)

    def test_native_boot_requires_both_images(self):
        self.args.boot_script = None
        self.args.boot_dtb = str(self.root / 'bl2.dtb')
        self.args.boot_bl2 = None
        with self.assertRaisesRegex(ValueError, 'both --boot-dtb and --boot-bl2'):
            deploy.validate_configuration(self.args)

    def test_cli_rejects_out_of_range_timeouts(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            deploy.build_parser().parse_args(['deploy', '--boot-timeout-seconds', '0'])
        self.assertEqual(error.exception.code, 2)


if __name__ == '__main__':
    unittest.main()