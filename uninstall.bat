@echo off
title Coffee Shop POS - Uninstaller
color 0C

echo.
echo ========================================
echo    Coffee Shop POS - Uninstaller
echo ========================================
echo.
echo This will completely remove the Coffee Shop POS system.
echo.
echo What will be removed:
echo - Installation folder: %USERPROFILE%\CoffeeShopPOS
echo - Desktop shortcuts
echo - All POS data and settings
echo.
set /p confirm="Are you sure you want to uninstall? (y/N): "
if /i not "%confirm%"=="y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Removing POS system...

:: Stop any running POS processes
echo Stopping POS processes...
taskkill /f /im python.exe >nul 2>&1

:: Remove desktop shortcuts
echo Removing desktop shortcuts...
if exist "%USERPROFILE%\Desktop\Coffee Shop POS.url" del "%USERPROFILE%\Desktop\Coffee Shop POS.url"
if exist "%USERPROFILE%\Desktop\Start Coffee Shop POS.bat" del "%USERPROFILE%\Desktop\Start Coffee Shop POS.bat"

:: Remove installation directory
echo Removing installation folder...
cd /d "%USERPROFILE%"
if exist "CoffeeShopPOS" (
    rmdir /s /q "CoffeeShopPOS"
    echo ✓ Installation folder removed
) else (
    echo Installation folder not found
)

echo.
echo ========================================
echo    Uninstall Complete!
echo ========================================
echo.
echo ✓ Coffee Shop POS has been completely removed.
echo.
echo All files, shortcuts, and data have been deleted.
echo.
pause
