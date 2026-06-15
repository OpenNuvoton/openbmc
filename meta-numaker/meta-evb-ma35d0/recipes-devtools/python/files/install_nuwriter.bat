@echo off
echo ============================================
echo  MA35D0 NuWriter Installation Script
echo ============================================
echo.

echo [1/2] Cloning NuWriter from GitHub...
git.exe clone https://github.com/OpenNuvoton/MA35D1_NuWriter
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to clone NuWriter repository
    pause
    exit /b 1
)

echo [2/2] Installing Python dependencies...
pip3 install pyusb usb crypto ecdsa crcmod tqdm pycryptodome
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)

echo.
echo ============================================
echo  NuWriter installation completed!
echo  Run nuwriter_program_spinand.bat to flash.
echo ============================================
pause
