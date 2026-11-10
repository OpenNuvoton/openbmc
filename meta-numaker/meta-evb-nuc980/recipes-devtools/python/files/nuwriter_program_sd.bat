@echo off
echo ============================================
echo  @MACHINE@ SD1/eMMC Programming Script
echo ============================================
echo.
echo Make sure the board is in USB download mode.
echo.

if not exist "NUC980_PyNuWriter\nuwriter.py" (
    echo ERROR: NUC980_PyNuWriter\nuwriter.py not found! Run install_nuwriter.bat first.
    pause
    exit /b 1
)

cd NUC980_PyNuWriter

echo [1/2] Initializing DDR and loading XUSB...
py -3 nuwriter.py -a @NUWRITER_DDR_IMG@
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: DDR initialization failed
    cd ..
    pause
    exit /b 1
)

echo [2/2] Programming SD1/eMMC pack image...
if not exist "..\nuwriter-pack-sd-@MACHINE@.bin" (
    echo ERROR: ..\nuwriter-pack-sd-@MACHINE@.bin not found!
    cd ..
    pause
    exit /b 1
)
py -3 nuwriter.py --ddr @NUWRITER_DDR_IMG@ -w sd "..\nuwriter-pack-sd-@MACHINE@.bin"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: SD1/eMMC programming failed
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo ============================================
echo  Programming completed successfully!
echo  Set Power-On Setting to SD/eMMC and reset the board.
echo ============================================
pause
exit /b 0
