#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CH341A (USB-SERIAL Mode) Reset Signal Generator for Linux /dev/ttyUSB0

Description:
------------
When operating under the standard USB-SERIAL mode, the CH341A functions as a
USB-to-UART bridge. In this mode, vendor-specific commands (such as 0xA0/0xA2
used to control D0~D5 GPIOs under parallel/I2C/SPI mode) are not available.
Writing raw bytes to the virtual serial port merely transmits data via TXD.

Controllable output pins in serial mode:
    RTS  - Controlled via ser.rts
    DTR  - Controlled via ser.dtr
    TXD  - Can be driven LOW using break_condition

Signal Polarity (TTL CH341A):
    ser.rts = True   -> RTS pin outputs LOW  (0V)
    ser.rts = False  -> RTS pin outputs HIGH (3.3V)
    DTR follows the same logic.

Active-Low Reset:
    assert   (pull low) -> ser.rts = True
    deassert (release)  -> ser.rts = False

Usage:
------
    python3 ch341_reset.py                   # Reset via /dev/ttyUSB0, RTS pin, 1.0s active-low pulse
    python3 ch341_reset.py --port /dev/ttyUSB0
    python3 ch341_reset.py --pin dtr         # Use DTR pin instead of RTS
    python3 ch341_reset.py --duration 0.5    # 500ms pulse duration
    python3 ch341_reset.py --toggle          # Slow toggle mode for multimeter/scope measurement
    python3 ch341_reset.py --list            # List available serial ports
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


def find_ch341_port():
    """Auto-detect CH341 serial port device."""
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").upper()
        hwid = (port.hwid or "").upper()
        if "CH341" in desc or "1A86" in hwid or "UART-LPT" in desc:
            return port.device

    if os.path.exists(DEFAULT_PORT):
        return DEFAULT_PORT

    return None


def list_ports():
    """List available serial ports and highlight CH341 devices."""
    print("Detected serial ports:")
    ports = serial.tools.list_ports.comports()
    # Sort USB / ACM ports first for readability on Linux
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

    def __init__(self, port=DEFAULT_PORT, pin=DEFAULT_PIN, active_low=ACTIVE_LOW):
        if pin not in ("rts", "dtr", "txd"):
            raise ValueError(f"Unsupported pin: {pin} (valid options: rts, dtr, txd)")
        self.port = port
        self.pin = pin
        self.active_low = active_low
        self.serial = None

    def connect(self):
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

    def _set_asserted(self, asserted):
        """
        asserted=True  -> Reset asserted (LOW when active-low)
        asserted=False -> Reset deasserted (HIGH when active-low)
        """
        if self.serial is None:
            raise RuntimeError("Serial port not connected")

        # PySerial: rts/dtr = True drives TTL pin LOW (0V)
        # break_condition = True drives TXD LOW
        level_flag = asserted if self.active_low else not asserted

        if self.pin == "rts":
            self.serial.rts = level_flag
        elif self.pin == "dtr":
            self.serial.dtr = level_flag
        else:  # txd
            self.serial.break_condition = level_flag

    def pulse(self, duration=DEFAULT_DURATION, settle_time=DEFAULT_SETTLE_TIME):
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

    def toggle_test(self, period=2.0, count=5):
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

    def close(self):
        if self.serial and self.serial.is_open:
            self._set_asserted(False)
            self.serial.close()
            print("Connection closed.")


def main():
    parser = argparse.ArgumentParser(
        description="CH341A (USB-SERIAL Mode) Reset Signal Generator for Linux"
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        help=f"Serial port device path (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--pin",
        choices=["rts", "dtr", "txd"],
        default=DEFAULT_PIN,
        help="Pin used for reset output (default: rts)",
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
    args = parser.parse_args()

    if args.list:
        list_ports()
        return 0

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
        print(f"Error: {e}")
        print()
        list_ports()
        return 1
    except KeyboardInterrupt:
        print("\nAborted by user.")
        return 130
    finally:
        ctl.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
