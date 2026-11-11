@echo off
cd /d "%~dp0"
echo ============================================
echo  MA35 NuWriter Installation Script
echo ============================================
echo.

echo [1/3] Cloning NuWriter from GitHub...
if exist "MA35D1_NuWriter\.git" (
    git.exe -C MA35D1_NuWriter pull
) else (
    git.exe clone https://github.com/OpenNuvoton/MA35D1_NuWriter
)
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to clone/update NuWriter repository
    pause
    exit /b 1
)

echo [2/3] Installing Python dependencies...
pip3 install pyusb usb crypto ecdsa crcmod tqdm pycryptodome python-pkcs11
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)

echo [3/3] Setting up libusb-1.0.dll...
if exist "%SystemRoot%\System32\libusb-1.0.dll" (
    echo libusb-1.0.dll is already installed in %SystemRoot%\System32.
) else (
    if exist "MA35D1_NuWriter\EXE\libusb-1.0.dll" (
        copy /Y "MA35D1_NuWriter\EXE\libusb-1.0.dll" "%SystemRoot%\System32\" >nul 2>&1
        if exist "%SystemRoot%\System32\libusb-1.0.dll" (
            echo Successfully installed libusb-1.0.dll to %SystemRoot%\System32.
        ) else (
            echo Requesting Administrator privileges to copy libusb-1.0.dll...
            powershell -Command "Start-Process cmd -ArgumentList '/c copy /y """"%~dp0MA35D1_NuWriter\EXE\libusb-1.0.dll"""" """"%SystemRoot%\System32\libusb-1.0.dll""""' -Verb RunAs -Wait" >nul 2>&1
            if exist "%SystemRoot%\System32\libusb-1.0.dll" (
                echo Successfully installed libusb-1.0.dll to %SystemRoot%\System32.
            ) else (
                echo WARNING: Failed to copy libusb-1.0.dll to %SystemRoot%\System32.
                echo          Please manually copy MA35D1_NuWriter\EXE\libusb-1.0.dll to C:\Windows\System32\
            )
        )
    ) else (
        echo WARNING: MA35D1_NuWriter\EXE\libusb-1.0.dll not found.
    )
)

echo.
echo ============================================
echo  NuWriter installation completed!
echo  Run nuwriter_program_spinand.bat, nuwriter_program_nand.bat, or nuwriter_program_sd.bat to flash.
echo ============================================
pause
