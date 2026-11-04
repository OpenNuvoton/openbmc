#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download-Mode Reset Hook using CH341A (USB-SERIAL Mode) on Linux (/dev/ttyUSB0)

Description:
------------
Controls the CH341A USB-to-UART adapter (default: /dev/ttyUSB0) to generate an
active-low hardware reset pulse (default: 1.0 second on RTS) so the target DUT
enters USB download mode.

Signal Polarity (TTL CH341A):
    ser.rts = True   -> RTS pin outputs LOW  (0V, reset asserted)
    ser.rts = False  -> RTS pin outputs HIGH (3.3V, reset deasserted)
    DTR follows the same logic; TXD uses break_condition.

Usage:
------
    # Called by deploy.py:
    python3 download_hook.py --media sd --deploy-option 7 --serial-port /dev/ttyACM0

    # Standalone CLI usage:
    python3 download_hook.py                           # 1.0s active-low pulse on /dev/ttyUSB0 (RTS)
    python3 download_hook.py --port /dev/ttyUSB0 --duration 1.0
    python3 download_hook.py --pin dtr
    python3 download_hook.py --toggle
    python3 download_hook.py --list
"""

import argparse
import os
import sys
import time

import serial
import serial.tools.list_ports

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_PIN = "rts"
DEFAULT_DURATION = 1.0
DEFAULT_SETTLE_TIME = 2.0
ACTIVE_LOW = True


def find_ch341_port() -> str | None:
    """Auto-detect CH341 serial port device."""
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").upper()
        hwid = (port.hwid or "").upper()
        if "CH341" in desc or "1A86" in hwid or "UART-LPT" in desc:
            return port.device

    if os.path.exists(DEFAULT_PORT):
        return DEFAULT_PORT

    return None


def list_ports() -> None:
    """List available serial ports and highlight CH341 devices."""
    print("Detected serial ports:")
    ports = serial.tools.list_ports.comports()
    ports.sort(key=lambda p: (0 if ("USB" in p.device or "ACM" in p.device) else 1, p.device))
    found = False
    for port in ports:
        desc = (port.description or "").upper()
        hwid = (port.hwid or "").upper()
        mark = ""
        if "CH341" in desc or "1A86" in hwid or "UART-LPT" in desc:
            mark = "   <-- CH341"
            found = True
        print(f"  {port.device}: {port.description} [{port.hwid}]{mark}")
    if not found:
        print(f"  (No CH341 device detected, default is {DEFAULT_PORT})")


class CH341Reset:
    """Generate reset pulse via CH341A serial control signals (RTS / DTR / TXD)."""

    def __init__(self, port: str = DEFAULT_PORT, pin: str = DEFAULT_PIN, active_low: bool = ACTIVE_LOW):
        if pin not in ("rts", "dtr", "txd"):
            raise ValueError(f"Unsupported pin: {pin} (valid options: rts, dtr, txd)")
        self.port = port
        self.pin = pin
        self.active_low = active_low
        self.serial: serial.Serial | None = None

    def connect(self) -> None:
        port = self.port or find_ch341_port() or DEFAULT_PORT
        if not os.path.exists(port) and port == DEFAULT_PORT:
            detected = find_ch341_port()
            if detected:
                port = detected

        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1,
                rtscts=False,
                dsrdtr=False,
            )
        except serial.SerialException as err:
            raise RuntimeError(
                f"Failed to open {port}: {err}\n"
                f"Ensure the device is connected and current user has dialout permissions."
            ) from err

        self.port = port
        print(f"Connected to: {port}  (Control pin: {self.pin.upper()})")

        # Initialize to deasserted state
        self._set_asserted(False)
        time.sleep(0.05)

    def _set_asserted(self, asserted: bool) -> None:
        """
        asserted=True  -> Reset asserted (LOW when active-low)
        asserted=False -> Reset deasserted (HIGH when active-low)
        """
        if self.serial is None:
            raise RuntimeError("Serial port not connected")

        level_flag = asserted if self.active_low else not asserted

        if self.pin == "rts":
            self.serial.rts = level_flag
        elif self.pin == "dtr":
            self.serial.dtr = level_flag
        else:  # txd
            self.serial.break_condition = level_flag

    def pulse(self, duration: float = DEFAULT_DURATION, settle_time: float = DEFAULT_SETTLE_TIME) -> None:
        """Generate a single reset pulse and wait for USB enumeration to settle."""
        polarity = "active-low" if self.active_low else "active-high"
        assert_level = "LOW (0V)" if self.active_low else "HIGH (3.3V)"
        release_level = "HIGH (3.3V)" if self.active_low else "LOW (0V)"

        print(f"Generating {duration}s reset pulse ({polarity}, {self.pin.upper()})")

        print(f"  assert   -> {self.pin.upper()} = {assert_level}")
        self._set_asserted(True)

        time.sleep(duration)

        print(f"  deassert -> {self.pin.upper()} = {release_level}")
        self._set_asserted(False)
        print(f"Waiting {settle_time}s for DUT USB enumeration...")
        time.sleep(settle_time)

        print("Reset pulse completed successfully.")

    def toggle_test(self, period: float = 2.0, count: int = 5) -> None:
        """Toggle the pin continuously for multimeter or oscilloscope measurement."""
        assert_level = "0V" if self.active_low else "3.3V"
        release_level = "3.3V" if self.active_low else "0V"

        print(f"Toggle test: {self.pin.upper()} toggling every {period}s for {count} cycles")
        print(f"Connect probe between {self.pin.upper()} pin and GND")
        for i in range(count):
            self._set_asserted(True)
            print(f"  [{i + 1}/{count}] assert   (expected: {assert_level})")
            time.sleep(period)
            self._set_asserted(False)
            print(f"  [{i + 1}/{count}] deassert (expected: {release_level})")
            time.sleep(period)

    def close(self) -> None:
        if self.serial and self.serial.is_open:
            self._set_asserted(False)
            self.serial.close()
            print("Connection closed.")


def reset_dut(
    port: str = DEFAULT_PORT,
    pin: str = DEFAULT_PIN,
    duration: float = DEFAULT_DURATION,
    settle_time: float = DEFAULT_SETTLE_TIME,
    active_low: bool = ACTIVE_LOW,
) -> None:
    """Trigger a hardware reset pulse on the DUT via CH341."""
    ctl = CH341Reset(port=port, pin=pin, active_low=active_low)
    try:
        ctl.connect()
        ctl.pulse(duration=duration, settle_time=settle_time)
    finally:
        ctl.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download-Mode Reset Hook via CH341A (USB-SERIAL Mode) for Linux"
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        help=f"CH341 serial port device path (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--pin",
        choices=["rts", "dtr", "txd"],
        default=DEFAULT_PIN,
        help=f"Pin used for reset output (default: {DEFAULT_PIN})",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION,
        help=f"Reset pulse duration in seconds (default: {DEFAULT_DURATION})",
    )
    parser.add_argument(
        "--settle-time",
        type=float,
        default=DEFAULT_SETTLE_TIME,
        help=f"Post-reset wait time for USB enumeration in seconds (default: {DEFAULT_SETTLE_TIME})",
    )
    parser.add_argument(
        "--active-high",
        action="store_true",
        help="Use active-high polarity (default: active-low)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List detected serial ports and exit",
    )
    parser.add_argument(
        "--toggle",
        action="store_true",
        help="Continuous toggle mode for voltage verification",
    )
    parser.add_argument(
        "--period",
        type=float,
        default=2.0,
        help="Toggle duration per level in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of toggle cycles (default: 5)",
    )
    # Arguments passed by deploy.py download_command()
    parser.add_argument(
        "--media",
        default=None,
        help="Target storage medium passed by deploy.py (e.g., sd, nand, spinand)",
    )
    parser.add_argument(
        "--deploy-option",
        default=None,
        help="Deploy option code passed by deploy.py (e.g., 3, 5, 7)",
    )
    parser.add_argument(
        "--serial-port",
        default=None,
        help="DUT UART console port passed by deploy.py",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        list_ports()
        return 0

    if args.media or args.deploy_option:
        print(
            f"Download hook invoked (media={args.media}, "
            f"deploy_option={args.deploy_option}, dut_uart={args.serial_port})"
        )

    ctl = CH341Reset(
        port=args.port,
        pin=args.pin,
        active_low=not args.active_high,
    )

    try:
        ctl.connect()
        if args.toggle:
            ctl.toggle_test(period=args.period, count=args.count)
        else:
            ctl.pulse(duration=args.duration, settle_time=args.settle_time)
    except (RuntimeError, ValueError, serial.SerialException) as e:
        print(f"Error: {e}", file=sys.stderr)
        print(file=sys.stderr)
        list_ports()
        return 1
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        return 130
    finally:
        ctl.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
