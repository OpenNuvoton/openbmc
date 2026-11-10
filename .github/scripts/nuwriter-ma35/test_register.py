import contextlib
import io
import struct
import sys
import unittest
from unittest.mock import Mock, patch

import nuwriter


class RegisterAccessTests(unittest.TestCase):
    def setUp(self):
        self.device = Mock()
        self.device.get_id.return_value = 0
        self.device.read.return_value = struct.pack('<II', nuwriter.ACK, 0x35A)
        self.device_list = patch.object(nuwriter, 'XUsbComList').start()
        self.addCleanup(patch.stopall)
        self.device_list.return_value.get_dev.return_value = [self.device]
        self.output = io.StringIO()
        self.stdout = contextlib.redirect_stdout(self.output)
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)

    def run_cli(self, *arguments):
        with patch.object(sys, 'argv', ['nuwriter.py', *arguments]):
            nuwriter.main()

    def test_read_packet_and_output(self):
        self.run_cli('-r', 'reg', '0x40460000')
        self.device.set_media.assert_called_once_with(9)
        self.device.write.assert_called_once_with(
            struct.pack('<QQII', 0x40460000, 4, nuwriter.ACT_READ, 0))
        self.device.read.assert_called_once_with(8)
        self.assertIn('[0x40460000] = 0x0000035A', self.output.getvalue())

    def test_write_packet_and_output_without_readback(self):
        for value in (0, 0x12345678, 0xFFFFFFFF):
            with self.subTest(value=value):
                self.device.reset_mock()
                self.run_cli('-w', 'REG', '0x40460000', str(value))
                self.device.write.assert_called_once_with(
                    struct.pack('<QQII', 0x40460000, 4, nuwriter.ACT_WRITE, value))
                self.device.read.assert_called_once_with(8)
                self.assertIn('<- 0x{:08X}'.format(value), self.output.getvalue())

    def test_address_boundaries(self):
        for address in (0, 0xFFFFFFFC):
            with self.subTest(address=address):
                nuwriter.do_reg_access(address)

    def test_invalid_access_never_opens_usb(self):
        for address, value in ((-4, None), (1, None), (0xFFFFFFFF, None),
                               (0x100000000, None), (0, -1), (0, 0x100000000)):
            with self.subTest(address=address, value=value):
                with self.assertRaises(ValueError):
                    nuwriter.do_reg_access(address, value)
        self.device_list.assert_not_called()

    def test_invalid_cli_never_opens_usb_or_attaches(self):
        cases = (
            ('-r', 'reg'),
            ('-r', 'reg', '0', 'extra'),
            ('-w', 'reg', '0'),
            ('-w', 'reg', '0', '1', 'extra'),
            ('-r', 'reg', 'invalid'),
            ('-r', 'reg', '1'),
            ('-w', 'reg', '0', '-1'),
            ('-w', 'reg', '0', '0x100000000'),
            ('-r', 'reg', '0', '-o', 'verify'),
            ('-w', 'reg', '0', '1', '-t', 'ddr'),
            ('-a', 'ddr.bin', '-r', 'reg', '1'),
        )
        with patch.object(nuwriter, 'do_attach') as attach:
            for arguments in cases:
                with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as result:
                        self.run_cli(*arguments)
                    self.assertEqual(result.exception.code, 2)
            attach.assert_not_called()
        self.device_list.assert_not_called()

    def test_attach_then_read(self):
        with patch.object(nuwriter.usb.core, 'find', return_value=object()), \
                patch.object(nuwriter, 'do_attach', return_value=0) as attach:
            self.run_cli('ddr.bin', '-a', '-r', 'reg', '0x40460000')
        attach.assert_called_once_with('ddr.bin', nuwriter.OPT_NONE)
        self.device.write.assert_called_once()

    def test_error_or_short_response_fails(self):
        for response in (b'', b'\xAA\x55', struct.pack('<I', nuwriter.ACK),
                         struct.pack('<II', 0xFFFFFFFF, 0)):
            with self.subTest(response=response):
                self.device.read.return_value = response
                with self.assertRaises(SystemExit) as result:
                    nuwriter.do_reg_access(0x40460000)
                self.assertEqual(result.exception.code, 1)

    def test_missing_device_fails(self):
        self.device_list.return_value.get_dev.return_value = []
        with self.assertRaises(SystemExit):
            nuwriter.do_reg_access(0x40460000)

    def test_mass_production_visits_all_devices_and_reports_failure(self):
        other = Mock()
        other.get_id.return_value = 1
        other.read.return_value = struct.pack('<II', 0xFFFFFFFF, 0)
        self.device_list.return_value.get_dev.return_value = [other, self.device]
        with patch.object(nuwriter, 'mp_mode', True):
            with self.assertRaises(SystemExit) as result:
                nuwriter.do_reg_access(0x40460000)
        self.assertEqual(result.exception.code, 1)
        self.device_list.assert_called_once_with(attach_all=True)
        self.device.write.assert_called_once()
        other.write.assert_called_once()

    def test_existing_flash_routing_is_unchanged(self):
        with patch.object(nuwriter, 'do_img_read') as read:
            self.run_cli('-r', 'spinor', '0x1000', '4', 'out.bin')
        read.assert_called_once_with(nuwriter.DEV_SPINOR, 0x1000, 'out.bin', 4, nuwriter.OPT_NONE)
        self.device_list.assert_not_called()

    def test_register_erase_is_rejected(self):
        with patch.object(nuwriter, 'do_img_erase') as erase:
            with self.assertRaises(SystemExit):
                self.run_cli('-e', 'reg', 'all')
        erase.assert_not_called()


if __name__ == '__main__':
    unittest.main()