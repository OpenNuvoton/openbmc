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

echo [2/2] Locating SD card WIC disk image...
set "WIC_FILE="
for %%f in ("..\obmc-phosphor-image-@MACHINE@*.wic") do (
    if /i "%%~xf"==".wic" set "WIC_FILE=%%f"
)

if exist "%WIC_FILE%" goto :do_flash

set "WIC_GZ="
for %%f in ("..\obmc-phosphor-image-@MACHINE@*.wic.gz") do (
    if /i "%%~xf"==".gz" set "WIC_GZ=%%f"
)

if not exist "%WIC_GZ%" goto :error_not_found

echo Found compressed WIC image: %WIC_GZ%
echo Decompressing...
py -3 -c "import gzip, shutil; shutil.copyfileobj(gzip.open(r'%WIC_GZ%', 'rb'), open(r'%WIC_GZ:~0,-3%', 'wb'))"
set "WIC_FILE=%WIC_GZ:~0,-3%"

:do_flash
if not exist "%WIC_FILE%" goto :error_not_found

echo Flashing %WIC_FILE% to SD/eMMC from offset 0x0...
py -3 nuwriter.py -w emmc 0x0 "%WIC_FILE%"
if %ERRORLEVEL% neq 0 (
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

:error_not_found
echo ERROR: obmc-phosphor-image-@MACHINE@.wic was not found!
echo Please make sure the WIC disk image is located in the firmware directory.
cd ..
pause
exit /b 1
