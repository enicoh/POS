@echo off
title Coffee Shop POS - Professional Installer
color 0A

echo.
echo ========================================
echo    Coffee Shop POS - Professional Installer
echo ========================================
echo.
echo This will install the Coffee Shop POS system with a professional GUI installer.
echo.
echo Features:
echo - Professional Windows GUI installer
echo - Automatic Python detection and installation guidance
echo - Comprehensive error handling
echo - Progress tracking
echo - One-click installation
echo.
echo Press any key to start the installer...
pause >nul

echo.
echo Starting Professional Installer...
echo.

:: Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is not available on this system!
    echo Please ensure PowerShell is installed and try again.
    echo.
    pause
    exit /b 1
)

:: Run the PowerShell installer
powershell -ExecutionPolicy Bypass -File "CoffeeShopPOS_Installer.ps1"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installation failed!
    echo Please check the error messages above and try again.
    echo.
    echo If you continue to have issues, you can use the original install.bat file
    echo as a fallback option.
    echo.
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo.
pause
