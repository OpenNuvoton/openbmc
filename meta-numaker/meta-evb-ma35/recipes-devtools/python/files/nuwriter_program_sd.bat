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

echo [2/2] Programming SD card...
if not exist ..\nuwriter-pack-sd-@MACHINE@.bin (
    echo ERROR: ..\nuwriter-pack-sd-@MACHINE@.bin not found
    cd ..
    pause
    exit /b 1
)
py -3 nuwriter.py -w emmc ../nuwriter-pack-sd-@MACHINE@.bin
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
