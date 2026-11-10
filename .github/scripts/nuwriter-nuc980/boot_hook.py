#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware Boot Reset Hook for NUC980 using CH341A (USB-SERIAL Mode).

Generates an active-low hardware reset pulse (default: 0.5s on RTS) so the NUC980
board reboots from the flashed storage medium (SPI-NAND or SD1/eMMC).
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NUC980 Hardware Boot Reset Hook")
    parser.add_argument("deploy_option_pos", nargs="?", type=int, help="Positional deploy option")
    parser.add_argument("--media", help="Deployment storage media (spinand, sd)")
    parser.add_argument("--deploy-option", type=int, help="Hardware boot DIP option")
    parser.add_argument("--serial-port", help="DUT serial console port")
    parser.add_argument("--port", help="CH341 reset adapter port")
    parser.add_argument("--pin", choices=["rts", "dtr", "txd"], default=DEFAULT_PIN)
    parser.add_argument("--duration", type=float, default=0.5, help="Reset pulse duration in seconds")
    parser.add_argument("--settle-time", type=float, default=0.5, help="Settle time in seconds")
    parser.add_argument("--active-high", action="store_true", help="Use active-high reset signal")
    parser.add_argument("--list", action="store_true", help="List available serial ports")
    args = parser.parse_args(argv)

    if args.list:
        list_ports()
        return 0

    ctl = CH341Reset(port=args.port, pin=args.pin, active_low=not args.active_high)
    try:
        ctl.connect()
        ctl.pulse(duration=args.duration)
        if args.settle_time > 0:
            time.sleep(args.settle_time)
        return 0
    except Exception as error:
        print(f"Error in boot hook: {error}", file=sys.stderr)
        return 1
    finally:
        ctl.close()


if __name__ == "__main__":
    sys.exit(main())

