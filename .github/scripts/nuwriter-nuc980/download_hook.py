#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download-Mode Reset Hook for NUC980 using CH341A (USB-SERIAL Mode).

Controls the CH341A USB-to-UART adapter to generate an active-low hardware reset
pulse (default: 1.0 second on RTS) so the NUC980 target enters USB download mode.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

try:
    from ch341_reset_uart import CH341Reset, DEFAULT_PIN, find_ch341_port, list_ports
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ch341_reset_uart import CH341Reset, DEFAULT_PIN, find_ch341_port, list_ports


def reset_dut(
    port: str | None = None,
    pin: str = DEFAULT_PIN,
    duration: float = 1.0,
    settle_time: float = 2.0,
    active_low: bool = True,
) -> None:
    ctl = CH341Reset(port=port, pin=pin, active_low=active_low)
    try:
        ctl.connect()
        ctl.pulse(duration=duration)
        if settle_time > 0:
            print(f"Waiting {settle_time}s for DUT USB enumeration...", flush=True)
            time.sleep(settle_time)
    finally:
        ctl.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NUC980 Download-Mode Reset Hook")
    parser.add_argument("--media", help="Deployment storage media (spinand, sd)")
    parser.add_argument("--deploy-option", type=int, help="Hardware boot DIP option")
    parser.add_argument("--serial-port", help="DUT serial console port")
    parser.add_argument("--port", help="CH341 reset adapter port")
    parser.add_argument("--pin", choices=["rts", "dtr", "txd"], default=DEFAULT_PIN)
    parser.add_argument("--duration", type=float, default=1.0, help="Reset pulse duration in seconds")
    parser.add_argument("--settle-time", type=float, default=2.0, help="USB settle time in seconds")
    parser.add_argument("--active-high", action="store_true", help="Use active-high reset signal")
    parser.add_argument("--list", action="store_true", help="List available serial ports")
    parser.add_argument("--toggle", action="store_true", help="Toggle pin for measurement testing")
    args = parser.parse_args(argv)

    if args.list:
        list_ports()
        return 0

    ctl = CH341Reset(port=args.port, pin=args.pin, active_low=not args.active_high)
    try:
        ctl.connect()
        if args.toggle:
            ctl.toggle_test()
        else:
            ctl.pulse(duration=args.duration)
            if args.settle_time > 0:
                print(f"Waiting {args.settle_time}s for DUT USB enumeration...", flush=True)
                time.sleep(args.settle_time)
        return 0
    except Exception as error:
        print(f"Error in download hook: {error}", file=sys.stderr)
        return 1
    finally:
        ctl.close()


if __name__ == "__main__":
    sys.exit(main())

