#!/usr/bin/env python3
"""
NuWriter Pack File Generator for NUC980

Implemented according to NUC980 NuWriter User Manual - Pack Mode chapter.

Pack file format:
  Pack Header (16 bytes):
    - Initial Marker: uint32 = 0x00000005
    - File Length: uint32 (total pack file size, 64KB-aligned)
    - File Number: uint32 (number of images)
    - Reserved: uint32 = 0xFFFFFFFF

  For each child image:
    Child Header (16 bytes):
      - File Length: uint32 (child data size)
      - File Address: uint32 (target burn address)
      - Image Type: uint32
      - Reserved: uint32 = 0xFFFFFFFF
    Child Data (File Length bytes)

"""

import struct
import argparse
import binascii
import os

# Image Type definitions (matching official NuWriter tool)
IMG_TYPE_DATA = 0
IMG_TYPE_ENV = 1
IMG_TYPE_LOADER = 2
IMG_TYPE_EMMC_PARTITION = 3

IMAGE_TYPE_MAP = {
    'data': IMG_TYPE_DATA,
    'loader': IMG_TYPE_LOADER,
    'env': IMG_TYPE_ENV,
    'environment': IMG_TYPE_ENV,
    'partition': IMG_TYPE_EMMC_PARTITION,
}

# Pack Header constants
PACK_INITIAL_MARKER = 0x00000005

# Loader Boot Code Header constants
BOOT_CODE_MARKER = 0x4E565420  # {0x20, 'T', 'V', 'N'} little-endian
DDR_INITIAL_MARKER = 0xAA55AA55


def parse_ddr_ini(ini_path):
    """
    Parse DDR parameter .ini file.
    Format: address=value (hex), first line is version number (excluded from DDR Counter).
    Returns list of (address, value) pairs (excluding the first version line).
    """
    pairs = []
    with open(ini_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and '=' in line]

    if not lines:
        return pairs

    # First line is DDR version, excluded from Counter
    for line in lines[1:]:
        parts = line.split('=')
        addr = int(parts[0].strip(), 16)
        val = int(parts[1].strip(), 16)
        pairs.append((addr, val))

    return pairs


def build_loader_header(image_data, execute_address, ddr_ini_path=None,
                        page_size=0x800, spare_area=0x40,
                        quad_read_cmd=0xFF, read_status_cmd=0xFF,
                        write_status_cmd=0xFF, status_value=0xFF,
                        dummy_byte=0xFF):
    """
    Build Loader type Boot Code Header + DDR parameters.

    Boot Code Header (32 bytes, offset 0x00-0x1F):
      0x00: Boot Code Marker (4 bytes)
      0x04: Execute Address (4 bytes)
      0x08: Image Size (4 bytes)
      0x0C: Reserved (4 bytes) = 0xFFFFFFFF
      0x10: Page Size (2 bytes)
      0x12: Spare Area (2 bytes)
      0x14: Quad Read cmd (1 byte)
      0x15: Read Status cmd (1 byte)
      0x16: Write Status cmd (1 byte)
      0x17: Status Value (1 byte)
      0x18: Dummy Byte (1 byte)
      0x19-0x1B: Reserved (3 bytes) = 0xFF
      0x1C-0x1F: Reserved (4 bytes) = 0xFFFFFFFF

    DDR Parameters (offset 0x20+):
      0x20: DDR Initial Marker (4 bytes) = 0x55AA55AA
      0x24: DDR Counter (4 bytes)
      0x28+: DDR Address/Value pairs (8 bytes each)
      Padding to 16-byte alignment with 0x00000000 dummy
    """
    image_size = len(image_data)

    # Boot Code Header row 0x00
    header = struct.pack('<IIII',
                         BOOT_CODE_MARKER,
                         execute_address,
                         image_size,
                         0xFFFFFFFF)

    # Boot Code Header row 0x10
    header += struct.pack('<HH', page_size, spare_area)
    header += struct.pack('<BBBBBBBBBBB',
                          quad_read_cmd, read_status_cmd,
                          write_status_cmd, status_value,
                          dummy_byte,
                          0xFF, 0xFF, 0xFF,  # Reserved bytes
                          0xFF, 0xFF, 0xFF)  # Part of reserved 4 bytes
    header += struct.pack('<B', 0xFF)  # Last reserved byte to make it 16 total

    # DDR Parameters
    ddr_pairs = []
    if ddr_ini_path and os.path.exists(ddr_ini_path):
        ddr_pairs = parse_ddr_ini(ddr_ini_path)

    ddr_counter = len(ddr_pairs)
    ddr_section = struct.pack('<II', DDR_INITIAL_MARKER, ddr_counter)

    for addr, val in ddr_pairs:
        ddr_section += struct.pack('<II', addr, val)

    # Pad DDR section to 16-byte alignment with 0x00000000 dummy
    while len(ddr_section) % 16 != 0:
        ddr_section += struct.pack('<I', 0x00000000)

    return header + ddr_section


def create_pack_file(images, output_path):
    """
    Create a NuWriter Pack file.

    Args:
      images: list of dict, each dict contains:
        - 'file': image file path
        - 'type': image type string ('data', 'loader', 'env', 'partition')
        - 'address': target burn address (int)
        - 'execute_address': execute address (Loader only, int, default 0x200)
        - 'ddr_ini': DDR parameter .ini file path (Loader only, optional)
        - 'page_size': SPI NAND page size (Loader only, optional)
        - 'spare_area': SPI NAND spare area (Loader only, optional)
      output_path: output pack file path
    """
    file_number = len(images)
    children = []  # list of (child_header_bytes, child_data_bytes)

    for img_info in images:
        file_path = img_info['file']
        img_type = IMAGE_TYPE_MAP.get(img_info['type'].lower(), IMG_TYPE_DATA)
        file_address = img_info.get('address', 0)

        with open(file_path, 'rb') as f:
            raw_data = f.read()

        if img_type == IMG_TYPE_LOADER:
            # Loader type: prepend Boot Code Header + DDR parameters
            exec_addr = img_info.get('execute_address', 0x200)
            ddr_ini = img_info.get('ddr_ini', None)
            page_size = img_info.get('page_size', 0x800)
            spare_area = img_info.get('spare_area', 0x40)

            loader_header = build_loader_header(
                raw_data, exec_addr, ddr_ini,
                page_size=page_size, spare_area=spare_area,
                quad_read_cmd=img_info.get('quad_read_cmd', 0xFF),
                read_status_cmd=img_info.get('read_status_cmd', 0xFF),
                write_status_cmd=img_info.get('write_status_cmd', 0xFF),
                status_value=img_info.get('status_value', 0xFF),
                dummy_byte=img_info.get('dummy_byte', 0xFF)
            )
            child_data = loader_header + raw_data
        elif img_type == IMG_TYPE_ENV:
            # Environment type: CRC32 (4 bytes) + env data (padded to 128KB for SPI NAND block size)
            # Convert newlines to \0 (U-Boot env format: null-separated key=value pairs)
            env_text = raw_data.replace(b'\r\n', b'\x00').replace(b'\n', b'\x00')
            # Strip trailing nulls before padding
            env_text = env_text.rstrip(b'\x00')
            # Pad env payload to 128KB-aligned (excluding CRC32 4 bytes)
            env_size = img_info.get('env_size', 0x20000 - 4)
            if env_size < len(env_text):
                env_size = ((len(env_text) + 4 + 0x1FFFF) // 0x20000) * 0x20000 - 4
            env_payload = env_text[:env_size]
            if len(env_payload) < env_size:
                env_payload += b'\x00' * (env_size - len(env_payload))
            crc = binascii.crc32(env_payload) & 0xFFFFFFFF
            child_data = struct.pack('<I', crc) + env_payload
        else:
            # Data type: use raw data directly
            child_data = raw_data

        child_file_length = len(child_data)

        # Child Header (16 bytes)
        child_header = struct.pack('<IIII',
                                   child_file_length,
                                   file_address,
                                   img_type,
                                   0xFFFFFFFF)  # Reserved

        children.append((child_header, child_data))

    # Calculate total length
    total_length = 16  # Pack Header
    for child_header, child_data in children:
        total_length += len(child_header) + len(child_data)

    # File Length field is 64KB-aligned
    aligned_length = ((total_length + 0xFFFF) // 0x10000) * 0x10000

    # Pack Header
    pack_header = struct.pack('<IIII',
                              PACK_INITIAL_MARKER,
                              aligned_length,
                              file_number,
                              0xFFFFFFFF)  # Reserved

    # Write file
    with open(output_path, 'wb') as f:
        f.write(pack_header)
        for child_header, child_data in children:
            f.write(child_header)
            f.write(child_data)

    print(f"Pack file created: {output_path}")
    print(f"  File Number: {file_number}")
    print(f"  File Length: 0x{aligned_length:08X} (64KB-aligned, actual={total_length})")
    for i, (img_info, (ch, cd)) in enumerate(zip(images, children)):
        print(f"  Child{i}: {os.path.basename(img_info['file'])}, "
              f"Type={img_info['type']}, "
              f"Address=0x{img_info.get('address', 0):08X}, "
              f"DataLen=0x{len(cd):08X}")


def main():
    parser = argparse.ArgumentParser(
        description='NuWriter Pack File Generator for NUC980')
    parser.add_argument('-o', '--output', required=True,
                        help='Output pack file path')
    parser.add_argument('-i', '--image', action='append', nargs='+',
                        metavar=('FILE', 'PARAM'),
                        help='Add image: FILE type=<data|loader|env> '
                             'address=<hex> [exec=<hex>] [ddr=<ini_path>] '
                             '[pagesize=<hex>] [spare=<hex>] '
                             '[quadread=<hex>] [dummy=<hex>]')

    args = parser.parse_args()

    if not args.image:
        parser.error("At least one -i/--image argument is required")

    images = []
    for img_args in args.image:
        if len(img_args) < 1:
            parser.error("Image requires at least a file path")

        img_info = {
            'file': img_args[0],
            'type': 'data',
            'address': 0,
            'execute_address': 0x200,
            'ddr_ini': None,
            'page_size': 0x800,
            'spare_area': 0x40,
            'quad_read_cmd': 0xFF,
            'read_status_cmd': 0xFF,
            'write_status_cmd': 0xFF,
            'status_value': 0xFF,
            'dummy_byte': 0xFF,
        }

        for param in img_args[1:]:
            if '=' not in param:
                continue
            key, value = param.split('=', 1)
            key = key.lower()
            if key == 'type':
                img_info['type'] = value
            elif key == 'address':
                img_info['address'] = int(value, 16)
            elif key == 'exec':
                img_info['execute_address'] = int(value, 16)
            elif key == 'ddr':
                img_info['ddr_ini'] = value
            elif key == 'pagesize':
                img_info['page_size'] = int(value, 16)
            elif key == 'spare':
                img_info['spare_area'] = int(value, 16)
            elif key == 'quadread':
                img_info['quad_read_cmd'] = int(value, 16)
            elif key == 'readstatus':
                img_info['read_status_cmd'] = int(value, 16)
            elif key == 'writestatus':
                img_info['write_status_cmd'] = int(value, 16)
            elif key == 'statusval':
                img_info['status_value'] = int(value, 16)
            elif key == 'dummy':
                img_info['dummy_byte'] = int(value, 16)
            elif key == 'envsize':
                img_info['env_size'] = int(value, 16)

        if not os.path.exists(img_info['file']):
            parser.error(f"File not found: {img_info['file']}")

        images.append(img_info)

    create_pack_file(images, args.output)


if __name__ == '__main__':
    main()
