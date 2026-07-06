@echo off
echo ============================================
echo  @MACHINE@ SPI-NAND Programming Script
echo ============================================
echo.
echo Make sure the board is in USB download mode.
echo.

cd MA35D1_NuWriter

echo [1/3] Initializing DDR...
py -3 nuwriter.py -a ddrimg/@NUWRITER_DDR_IMG@
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
py -3 nuwriter.py -w spinand ../nuwriter-pack-@MACHINE@.bin
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
