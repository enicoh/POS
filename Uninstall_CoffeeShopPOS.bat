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
echo WARNING: This will delete:
echo - All application files
echo - Database and user data
echo - Desktop shortcuts
echo - Installation directory
echo.
set /p confirm="Are you sure you want to uninstall? (y/N): "
if /i not "%confirm%"=="y" (
    echo.
    echo Uninstall cancelled.
    echo.
    pause
    exit /b 0
)

echo.
echo ========================================
echo    Starting Uninstallation...
echo ========================================
echo.

:: Stop any running POS processes
echo [1/5] Stopping running processes...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Stopped running processes
) else (
    echo [INFO] No running processes found
)

:: Remove desktop shortcuts
echo.
echo [2/5] Removing desktop shortcuts...
if exist "%USERPROFILE%\Desktop\Coffee Shop POS.lnk" (
    del "%USERPROFILE%\Desktop\Coffee Shop POS.lnk"
    echo [OK] Removed desktop shortcut
) else (
    echo [INFO] No desktop shortcut found
)

if exist "%USERPROFILE%\Desktop\Coffee Shop POS.bat" (
    del "%USERPROFILE%\Desktop\Coffee Shop POS.bat"
    echo [OK] Removed desktop batch file
)

:: Remove installation directory
echo.
echo [3/5] Removing installation directory...
set "INSTALL_DIR=%USERPROFILE%\Desktop\CoffeeShopPOS"
if exist "%INSTALL_DIR%" (
    echo Removing: %INSTALL_DIR%
    rmdir /s /q "%INSTALL_DIR%"
    if %errorlevel% equ 0 (
        echo [OK] Installation directory removed
    ) else (
        echo [ERROR] Failed to remove installation directory
        echo You may need to manually delete: %INSTALL_DIR%
    )
) else (
    echo [INFO] Installation directory not found
)

:: Remove any remaining files in current directory (if running from installation)
echo.
echo [4/5] Cleaning up current directory...
if exist "start_pos.bat" del "start_pos.bat"
if exist "uninstall.bat" del "uninstall.bat"
if exist "venv" rmdir /s /q "venv"
if exist "instance" rmdir /s /q "instance"
echo [OK] Current directory cleaned

:: Final cleanup
echo.
echo [5/5] Final cleanup...
echo [OK] Cleanup completed

echo.
echo ========================================
echo    Uninstallation Complete!
echo ========================================
echo.
echo [SUCCESS] Coffee Shop POS has been completely removed.
echo.
echo Removed:
echo - Application files and folders
echo - Database and user data
echo - Desktop shortcuts
echo - Virtual environment
echo.
echo Thank you for using Coffee Shop POS!
echo.
pause
