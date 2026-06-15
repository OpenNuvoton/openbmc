#!/usr/bin/env python3
"""
NuWriter Pack File Reader/Parser for NUC980

Implemented according to NUC980 NuWriter User Manual - Pack Mode chapter.

Reads a NuWriter Pack file and displays Pack Header and Child Header field information.
"""

import struct
import argparse
import binascii
import os

# Image Type definitions (matching official NuWriter tool)
IMAGE_TYPE_NAMES = {
    0: 'Data',
    1: 'Environment',
    2: 'Loader',
    3: 'eMMC/SD Partition',
}

# Pack Header constants
PACK_INITIAL_MARKER = 0x00000005
BOOT_CODE_MARKER = 0x4E565420  # {0x20, 'T', 'V', 'N'}
DDR_INITIAL_MARKER = 0xAA55AA55


def parse_loader_header(data, offset=0):
    """
    Parse Loader type Boot Code Header + DDR parameters.
    Returns a dict with parsed fields.
    """
    info = {}

    # Boot Code Header (0x00-0x1F)
    marker, exec_addr, img_size, reserved = struct.unpack_from('<IIII', data, offset)
    info['boot_code_marker'] = marker
    info['boot_code_marker_valid'] = (marker == BOOT_CODE_MARKER)
    info['execute_address'] = exec_addr
    info['image_size'] = img_size
    info['reserved_0c'] = reserved

    # Row 0x10
    page_size, spare_area = struct.unpack_from('<HH', data, offset + 0x10)
    spi_params = struct.unpack_from('<BBBBB', data, offset + 0x14)

    info['page_size'] = page_size
    info['spare_area'] = spare_area
    info['quad_read_cmd'] = spi_params[0]
    info['read_status_cmd'] = spi_params[1]
    info['write_status_cmd'] = spi_params[2]
    info['status_value'] = spi_params[3]
    info['dummy_byte'] = spi_params[4]

    # DDR Parameters (offset 0x20)
    ddr_marker, ddr_counter = struct.unpack_from('<II', data, offset + 0x20)
    info['ddr_initial_marker'] = ddr_marker
    info['ddr_initial_marker_valid'] = (ddr_marker == DDR_INITIAL_MARKER)
    info['ddr_counter'] = ddr_counter

    # DDR Address/Value pairs
    ddr_pairs = []
    pair_offset = offset + 0x28
    for i in range(ddr_counter):
        if pair_offset + 8 <= len(data):
            addr, val = struct.unpack_from('<II', data, pair_offset)
            ddr_pairs.append((addr, val))
            pair_offset += 8
    info['ddr_pairs'] = ddr_pairs

    # Calculate DDR section total size after alignment
    ddr_section_size = 8 + ddr_counter * 8  # marker + counter + pairs
    while ddr_section_size % 16 != 0:
        ddr_section_size += 4

    info['header_total_size'] = 0x20 + ddr_section_size  # Boot Code Header + DDR
    info['data_offset'] = info['header_total_size']  # raw binary offset within child data

    return info


def read_pack_file(pack_path, show_ddr=False):
    """
    Read and parse a NuWriter Pack file, displaying all field information.
    """
    if not os.path.exists(pack_path):
        print(f"Error: File not found: {pack_path}")
        return

    with open(pack_path, 'rb') as f:
        data = f.read()

    file_size = len(data)

    if file_size < 16:
        print("Error: File too small, not a valid Pack file")
        return

    # ===== Pack Header =====
    initial_marker, file_length, file_number, reserved = struct.unpack_from('<IIII', data, 0)

    print("=" * 60)
    print("Pack Header (offset 0x00, 16 bytes)")
    print("=" * 60)
    print(f"  Initial Marker : 0x{initial_marker:08X}", end='')
    if initial_marker == PACK_INITIAL_MARKER:
        print(" (Valid)")
    else:
        print(f" (INVALID! Expected 0x{PACK_INITIAL_MARKER:08X})")
    print(f"  File Length    : 0x{file_length:08X} ({file_length} bytes, "
          f"aligned to 64KB)")
    print(f"  File Number    : {file_number}")
    print(f"  Reserved       : 0x{reserved:08X}")
    print(f"  Actual FileSize: 0x{file_size:08X} ({file_size} bytes)")
    print()

    if initial_marker != PACK_INITIAL_MARKER:
        print("Warning: Initial Marker mismatch, may not be a valid Pack file")
        print()

    # ===== Child Headers =====
    offset = 16  # Start after Pack Header

    for i in range(file_number):
        if offset + 16 > file_size:
            print(f"Error: Insufficient data to read Child{i} Header (offset=0x{offset:08X})")
            break

        child_file_length, child_file_address, child_image_type, child_reserved = \
            struct.unpack_from('<IIII', data, offset)

        type_name = IMAGE_TYPE_NAMES.get(child_image_type,
                                          f'Unknown({child_image_type})')

        print("-" * 60)
        print(f"Child{i} Header (offset 0x{offset:08X}, 16 bytes)")
        print("-" * 60)
        print(f"  File Length    : 0x{child_file_length:08X} "
              f"({child_file_length} bytes)")
        print(f"  File Address   : 0x{child_file_address:08X} "
              f"(target burn address)")
        print(f"  Image Type     : 0x{child_image_type:08X} ({type_name})")
        print(f"  Reserved       : 0x{child_reserved:08X}")

        child_data_offset = offset + 16  # child data start

        print(f"  Data Offset    : 0x{child_data_offset:08X} "
              f"(child data start in pack file)")

        # If Loader type, parse Boot Code Header
        if child_image_type == 2 and child_data_offset + 0x28 <= file_size:
            loader_info = parse_loader_header(data, child_data_offset)
            print()
            print(f"  [Loader Boot Code Header]")
            print(f"    Boot Code Marker  : 0x{loader_info['boot_code_marker']:08X}", end='')
            if loader_info['boot_code_marker_valid']:
                print(" (Valid: NVT\\x20)")
            else:
                print(" (INVALID)")
            print(f"    Execute Address   : 0x{loader_info['execute_address']:08X}")
            print(f"    Image Size        : 0x{loader_info['image_size']:08X} "
                  f"({loader_info['image_size']} bytes)")
            print(f"    Page Size         : 0x{loader_info['page_size']:04X}")
            print(f"    Spare Area        : 0x{loader_info['spare_area']:04X}")
            print(f"    Quad Read Cmd     : 0x{loader_info['quad_read_cmd']:02X}")
            print(f"    Read Status Cmd   : 0x{loader_info['read_status_cmd']:02X}")
            print(f"    Write Status Cmd  : 0x{loader_info['write_status_cmd']:02X}")
            print(f"    Status Value      : 0x{loader_info['status_value']:02X}")
            print(f"    Dummy Byte        : 0x{loader_info['dummy_byte']:02X}")
            print()
            print(f"  [DDR Parameters]")
            print(f"    DDR Init Marker   : 0x{loader_info['ddr_initial_marker']:08X}", end='')
            if loader_info['ddr_initial_marker_valid']:
                print(" (Valid)")
            else:
                print(" (INVALID)")
            print(f"    DDR Counter       : {loader_info['ddr_counter']}")
            print(f"    Header Total Size : 0x{loader_info['header_total_size']:08X} "
                  f"({loader_info['header_total_size']} bytes)")
            print(f"    Raw Binary Offset : 0x{child_data_offset + loader_info['data_offset']:08X} "
                  f"(in pack file)")
            print(f"    Raw Binary Size   : 0x{loader_info['image_size']:08X} "
                  f"({loader_info['image_size']} bytes)")

            if loader_info['ddr_pairs']:
                print()
                print(f"    DDR Pairs ({loader_info['ddr_counter']} entries):")
                for j, (addr, val) in enumerate(loader_info['ddr_pairs']):
                    print(f"      [{j:3d}] Address=0x{addr:08X}  Value=0x{val:08X}")

        # If Environment type, show CRC32 info
        if child_image_type == 1 and child_file_length >= 4:
            crc_stored = struct.unpack_from('<I', data, child_data_offset)[0]
            env_payload = data[child_data_offset + 4:child_data_offset + child_file_length]
            crc_computed = binascii.crc32(env_payload) & 0xFFFFFFFF
            print()
            print(f"  [Environment]")
            print(f"    Stored CRC32  : 0x{crc_stored:08X}")
            print(f"    Computed CRC32: 0x{crc_computed:08X}", end='')
            if crc_stored == crc_computed:
                print(" (Valid)")
            else:
                print(" (MISMATCH!)")
            print(f"    Env Data Size : 0x{len(env_payload):08X} "
                  f"({len(env_payload)} bytes)")

        print()

        # Move to next Child
        offset = child_data_offset + child_file_length

    print("=" * 60)
    print("End of Pack File")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='NuWriter Pack File Reader/Parser for NUC980')
    parser.add_argument('pack_file', help='NuWriter Pack file path')
    parser.add_argument('--ddr', action='store_true',
                        help='Show full DDR parameter list')

    args = parser.parse_args()
    read_pack_file(args.pack_file, show_ddr=args.ddr)


if __name__ == '__main__':
    main()
