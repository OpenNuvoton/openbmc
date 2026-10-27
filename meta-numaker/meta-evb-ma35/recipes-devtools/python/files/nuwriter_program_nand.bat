@echo off
echo ============================================
echo  @MACHINE@ NAND Programming Script
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

echo [2/3] Erasing entire NAND flash...
py -3 nuwriter.py -e nand all
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: NAND erase failed
    cd ..
    pause
    exit /b 1
)

echo [3/3] Programming and verifying NAND flash...
if not exist ..\nuwriter-pack-nand-@MACHINE@.bin (
    echo ERROR: ..\nuwriter-pack-nand-@MACHINE@.bin not found
    cd ..
    pause
    exit /b 1
)
py -3 nuwriter.py -w nand ../nuwriter-pack-nand-@MACHINE@.bin
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: NAND programming/verification failed
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo ============================================
echo  Programming completed successfully!
echo  Reset the board to boot from NAND.
echo ============================================
pause
