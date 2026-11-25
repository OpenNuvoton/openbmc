@echo off
echo ============================================
echo  @MACHINE@ SD Card Programming Script
echo ============================================
echo.
echo Make sure the board is in USB download mode.
echo.

cd MA35D1_NuWriter

echo [1/2] Initializing DDR...
py -3 nuwriter.py -a ddrimg/@NUWRITER_DDR_IMG@
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: DDR initialization failed
    cd ..
    pause
    exit /b 1
)

echo [2/2] Programming SD/eMMC WIC disk image...
set "WIC_FILE=..\obmc-phosphor-image-@MACHINE@.wic"
if not exist "%WIC_FILE%" (
    echo ERROR: obmc-phosphor-image-@MACHINE@.wic was not found!
    echo Please make sure the WIC disk image is located in the firmware directory.
    cd ..
    pause
    exit /b 1
)

echo Flashing %WIC_FILE% to SD/eMMC from offset 0x0...
py -3 nuwriter.py -w emmc 0x0 "%WIC_FILE%"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: SD card programming failed
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo ============================================
echo  Programming completed successfully!
echo  Reset the board to boot from SD card.
echo ============================================
pause
exit /b 0
