@echo off
echo ============================================
echo  NUC980 NuWriter Installation Script
echo ============================================
echo.

echo [1/2] Cloning NUC980_PyNuWriter from GitHub...
if exist "NUC980_PyNuWriter\.git" (
    git.exe -C NUC980_PyNuWriter pull
) else (
    git.exe clone https://github.com/wosayttn/NUC980_PyNuWriter
)
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to clone/update NUC980_PyNuWriter repository
    pause
    exit /b 1
)

echo [2/2] Installing Python dependencies...
pip3 install -r NUC980_PyNuWriter\requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)

echo.
echo ============================================
echo  NuWriter installation completed!
echo  Run nuwriter_program_spinand.bat or nuwriter_program_sd.bat to flash.
echo ============================================
pause
