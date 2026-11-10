# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time
from UnpackImage import UnpackImage

def calculate_timeout(size_bytes):
    """
    Calculate timeout: 2.5s per 1 MB, with a minimum buffer of 2.0s.
    """
    mb_size = size_bytes / (1024.0 * 1024.0)
    calc_time = mb_size * 5.0
    return max(2.0, calc_time) + 8.0

def verify_in_memory():
    # 1. Handle Command Line Arguments
    if len(sys.argv) < 3:
        print("Usage: python verify_pack.py <flash_type> <your_pack_file.bin>")
        sys.exit(1)

    FLASH_TYPE = sys.argv[1]
    PACK_FILE = sys.argv[2]

    if not os.path.exists(PACK_FILE):
        print(f"Error: Pack file '{PACK_FILE}' not found.")
        sys.exit(1)

    # --- Configuration ---
    # Determine the actual base directory (where the .exe or .py resides)
    if getattr(sys, 'frozen', False):
        # If running as a bundled EXE, use sys.executable
        # This points to: C:\Your\Path\To\verify_pack.exe
        BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # If running as a normal Python script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    NUWRITER_EXE = os.path.join(BASE_DIR, "EXE", "NuWriter_MA35.exe")
    BUFFER_FILE = "flash_temp_buf.dat"

    if not os.path.exists(NUWRITER_EXE):
        print(f"Error: Cannot find {NUWRITER_EXE}")
        sys.exit(1)

    # Load Pack File
    print(f"Loading Pack: {PACK_FILE}")
    try:
        packer = UnpackImage(PACK_FILE, nocrc=0)
    except Exception as e:
        print(f"Failed to initialize UnpackImage: {e}")
        sys.exit(1)
    
    # 2. Adjust Table Header (Added Time column)
    print("-" * 100)
    print(f"{'Index':<6} | {'Flash Offset':<15} | {'Size (Hex)':<12} | {'Time (s)':<10} | {'Result'}")
    print("-" * 100)

    pass_count = 0
    fail_count = 0
    error_occurred = False

    for i in range(packer.img_count()):
        length, flash_offset, img_type = packer.img_attr(i)
        
        # Prepare the line prefix
        prefix = f"img{i:<3} | {hex(flash_offset):<15} | {hex(length):<12} | "
        sys.stdout.write(prefix)
        sys.stdout.flush()

        if os.path.exists(BUFFER_FILE):
            os.remove(BUFFER_FILE)

        current_timeout = calculate_timeout(length)
        cmd = [NUWRITER_EXE, "-r", FLASH_TYPE, hex(flash_offset), hex(length), BUFFER_FILE]
        
        start_time = time.time()  # Start timing
        elapsed = 0.0

        try:
            # Step A: Execute NuWriter to read flash
            subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.STDOUT,
                timeout=current_timeout
            )
            
            elapsed = time.time() - start_time # Calculate elapsed time for hardware reading
            
            if not os.path.exists(BUFFER_FILE):
                raise Exception("No data read from Flash")

            # Step B: Read to memory and compare
            with open(BUFFER_FILE, "rb") as f:
                flash_mem_data = f.read()
            
            # Immediately delete temp file
            try:
                os.remove(BUFFER_FILE)
            except:
                pass

            expected_data = packer.img_content(i, 0, length)

            if flash_mem_data != expected_data:
                for b in range(len(expected_data)):
                    if b >= len(flash_mem_data) or expected_data[b] != flash_mem_data[b]:
                        raise Exception(f"Mismatch at {hex(b)}")

            # Report Success with Time
            sys.stdout.write(f"{elapsed:<10.1f} | PASS\n")
            pass_count += 1

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            sys.stdout.write(f"{elapsed:<10.1f} | FAIL (Timeout after {current_timeout:.1f}s)\n")
            fail_count += 1
            error_occurred = True
        except Exception as e:
            elapsed = time.time() - start_time
            sys.stdout.write(f"{elapsed:<10.1f} | FAIL ({str(e)})\n")
            fail_count += 1
            error_occurred = True

        if error_occurred:
            break

    # --- Final Summary ---
    print("-" * 100)
    print(f"Final Report: {pass_count} PASSED, {fail_count} FAILED.")

    if os.path.exists(BUFFER_FILE):
        try:
            os.remove(BUFFER_FILE)
        except:
            pass

    sys.exit(1 if fail_count > 0 else 0)

if __name__ == "__main__":
    verify_in_memory()
