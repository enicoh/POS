@echo off
title Coffee Shop POS Installer
color 0B
echo.
echo ========================================
echo    Coffee Shop POS Installer
echo ========================================
echo.
echo Launching installer...
echo.

:: Check if script exists
if not exist "CoffeeShopPOS_Installer.ps1" (
    echo ERROR: CoffeeShopPOS_Installer.ps1 not found!
    echo Please make sure you are running this file from the same folder as the installer script.
    pause
    exit /b 1
)

:: Launch PowerShell script with ExecutionPolicy Bypass
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& '.\CoffeeShopPOS_Installer.ps1'"

if %errorlevel% neq 0 (
    echo.
    echo Installer encountered an error.
    pause
)
