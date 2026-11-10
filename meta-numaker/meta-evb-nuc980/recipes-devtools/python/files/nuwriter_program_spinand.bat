@echo off
echo ============================================
echo  @MACHINE@ SPI-NAND Programming Script
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

echo [1/3] Initializing DDR and loading XUSB...
py -3 nuwriter.py -a @NUWRITER_DDR_IMG@
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: DDR initialization failed
    cd ..
    pause
    exit /b 1
)

echo [2/3] Erasing entire SPI-NAND flash...
py -3 nuwriter.py -e spinand all
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: SPI-NAND erase failed
    cd ..
    pause
    exit /b 1
)

echo [3/3] Programming SPI-NAND flash...
if not exist "..\nuwriter-pack-spinand-@MACHINE@.bin" (
    echo ERROR: ..\nuwriter-pack-spinand-@MACHINE@.bin not found
    cd ..
    pause
    exit /b 1
)
py -3 nuwriter.py --ddr @NUWRITER_DDR_IMG@ -w spinand "..\nuwriter-pack-spinand-@MACHINE@.bin"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: SPI-NAND programming failed
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo ============================================
echo  Programming completed successfully!
echo  Reset the board to boot from SPI-NAND.
echo ============================================
pause
