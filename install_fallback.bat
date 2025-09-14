@echo off
title Coffee Shop POS - Installer
color 0A

echo.
echo ========================================
echo    Coffee Shop POS - Installer
echo ========================================
echo.
echo This will install the Coffee Shop POS system on your computer.
echo.
echo What this installer does:
echo - Creates a dedicated POS folder
echo - Checks Python installation
echo - Sets up virtual environment
echo - Installs all dependencies
echo - Sets up the database
echo - Creates desktop shortcuts
echo - Creates uninstaller
echo.
echo Press any key to start installation...
pause >nul

echo.
echo ========================================
echo    Starting Installation...
echo ========================================
echo.

:: Set installation directory (desktop)
set "INSTALL_DIR=%USERPROFILE%\Desktop\CoffeeShopPOS"
set "SOURCE_DIR=%CD%"

echo [1/9] Preparing installation...
echo ✓ Source directory: %SOURCE_DIR%
echo ✓ Installation directory: %INSTALL_DIR%

:: Create installation directory
echo.
echo [2/9] Creating installation directory...
if exist "%INSTALL_DIR%" (
    echo Directory already exists. Removing old installation...
    rmdir /s /q "%INSTALL_DIR%"
)
mkdir "%INSTALL_DIR%"
if %errorlevel% neq 0 (
    echo ERROR: Failed to create installation directory!
    pause
    exit /b 1
)
echo ✓ Installation directory created: %INSTALL_DIR%

:: Copy necessary files to installation directory
echo.
echo [3/9] Copying application files...
xcopy "%SOURCE_DIR%\app.py" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\config.py" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\models.py" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\populate_sample_data.py" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\pos_routes.py" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\routes.py" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\requirements.txt" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\setup_database.py" "%INSTALL_DIR%\" /Y >nul
xcopy "%SOURCE_DIR%\static" "%INSTALL_DIR%\static\" /E /I /Y >nul
xcopy "%SOURCE_DIR%\templates" "%INSTALL_DIR%\templates\" /E /I /Y >nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy files!
    pause
    exit /b 1
)
echo ✓ Application files copied successfully

:: Change to installation directory
cd /d "%INSTALL_DIR%"

:: Check if Python is installed
echo.
echo [4/9] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Python is installed
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python version: %PYTHON_VERSION%

:: Create virtual environment
echo.
echo [5/9] Creating virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment!
        echo This might be due to insufficient permissions or Python issues.
        echo Please ensure Python is properly installed and you have write permissions.
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

:: Verify virtual environment was created properly
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment was not created properly!
    echo The venv\Scripts\activate.bat file is missing.
    echo Please check Python installation and try again.
    pause
    exit /b 1
)
echo ✓ Virtual environment verified

:: Activate virtual environment and install dependencies
echo.
echo [6/9] Installing dependencies...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

:: Upgrade pip first
python -m pip install --upgrade pip >nul 2>&1

:: Install all requirements
echo Installing Python packages...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo ✓ Dependencies installed successfully

:: Initialize database
echo.
echo [7/9] Setting up database...
python setup_database.py
if %errorlevel% neq 0 (
    echo ERROR: Database setup failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

:: Populate sample data
echo.
echo [8/9] Adding sample data...
python populate_sample_data.py >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Failed to populate sample data, but continuing...
) else (
    echo ✓ Sample data added
)

:: Create start script and desktop shortcut
echo.
echo [9/9] Creating start script and desktop shortcut...
(
echo @echo off
echo title Coffee Shop POS System
echo color 0B
echo echo.
echo echo ========================================
echo echo    Coffee Shop POS System
echo echo ========================================
echo echo.
echo echo Starting POS System...
echo echo.
echo.
echo :: Display current directory for debugging
echo echo Current directory: %%CD%%
echo echo.
echo.
echo :: Check if virtual environment exists
echo if not exist "venv" ^(
echo     echo ERROR: Virtual environment not found!
echo     echo Current directory: %%CD%%
echo     echo Please run install.bat first to set up the system.
echo     echo.
echo     echo If you already ran install.bat, try:
echo     echo 1. Make sure you're in the correct directory
echo     echo 2. Check if the venv folder exists
echo     echo 3. Re-run install.bat
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo :: Check if virtual environment activation script exists
echo if not exist "venv\Scripts\activate.bat" ^(
echo     echo ERROR: Virtual environment activation script not found!
echo     echo The venv\Scripts\activate.bat file is missing.
echo     echo Please re-run install.bat to recreate the virtual environment.
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo :: Check if app.py exists
echo if not exist "app.py" ^(
echo     echo ERROR: app.py not found!
echo     echo Please make sure you're in the correct directory.
echo     echo Current directory: %%CD%%
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Virtual environment found and verified.
echo echo.
echo echo The system will be available at: http://localhost:8080
echo echo.
echo echo Default login credentials:
echo echo Admin: admin / admin
echo echo Cashier: seller / seller
echo echo.
echo echo Opening web browser in 3 seconds...
echo echo Press Ctrl+C to stop the server
echo echo.
echo.
echo :: Start the app in background and open browser
echo start /b call venv\Scripts\activate.bat ^&^& python app.py
echo.
echo :: Wait a moment for the server to start
echo timeout /t 3 /nobreak ^>nul
echo.
echo :: Open the browser
echo start http://localhost:8080
echo.
echo :: Wait for user to press a key to stop
echo echo.
echo echo Press any key to stop the POS system...
echo pause ^>nul
echo.
echo :: Stop the background process
echo taskkill /f /im python.exe ^>nul 2^>^&1
echo.
echo echo.
echo echo POS System stopped.
) > "start_pos.bat"
echo ✓ Start script created

:: Create desktop shortcuts
set DESKTOP=%USERPROFILE%\Desktop

echo Creating desktop shortcut...

:: First, try to create a VBS script for desktop shortcut with icon
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP%\Coffee Shop POS.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\start_pos.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Coffee Shop POS System" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%INSTALL_DIR%\static\placeholder-coffee.svg" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

:: Run the VBS script to create the shortcut
cscript //nologo "%TEMP%\CreateShortcut.vbs"
if %errorlevel% neq 0 (
    echo VBS shortcut creation failed, trying alternative method...
    
    :: Try PowerShell method
    powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Coffee Shop POS.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\start_pos.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Coffee Shop POS System'; $Shortcut.IconLocation = '%INSTALL_DIR%\static\placeholder-coffee.svg'; $Shortcut.Save()" >nul 2>&1
    
    if %errorlevel% neq 0 (
        echo PowerShell method failed, creating basic batch file shortcut...
        echo @echo off > "%DESKTOP%\Coffee Shop POS.bat"
        echo title Coffee Shop POS System >> "%DESKTOP%\Coffee Shop POS.bat"
        echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\Coffee Shop POS.bat"
        echo start_pos.bat >> "%DESKTOP%\Coffee Shop POS.bat"
        echo ✓ Basic desktop shortcut created
    ) else (
        echo ✓ Desktop shortcut with icon created (PowerShell method)
    )
) else (
    echo ✓ Desktop shortcut with icon created (VBS method)
)

:: Clean up temporary VBS file
del "%TEMP%\CreateShortcut.vbs" >nul 2>&1

:: Verify shortcut was created
if exist "%DESKTOP%\Coffee Shop POS.lnk" (
    echo ✓ Desktop shortcut verified: Coffee Shop POS.lnk
) else if exist "%DESKTOP%\Coffee Shop POS.bat" (
    echo ✓ Desktop shortcut verified: Coffee Shop POS.bat
) else (
    echo ❌ WARNING: No desktop shortcut was created!
    echo You can manually create one by copying start_pos.bat to your desktop
)

:: Create uninstaller
echo.
echo Creating uninstaller...
echo @echo off > uninstall.bat
echo title Coffee Shop POS - Uninstaller >> uninstall.bat
echo color 0C >> uninstall.bat
echo echo. >> uninstall.bat
echo echo ======================================== >> uninstall.bat
echo echo    Coffee Shop POS - Uninstaller >> uninstall.bat
echo echo ======================================== >> uninstall.bat
echo echo. >> uninstall.bat
echo echo This will completely remove the Coffee Shop POS system. >> uninstall.bat
echo echo. >> uninstall.bat
echo set /p confirm="Are you sure you want to uninstall? (y/N): " >> uninstall.bat
echo if /i not "%%confirm%%"=="y" ( >> uninstall.bat
echo     echo Uninstall cancelled. >> uninstall.bat
echo     pause >> uninstall.bat
echo     exit /b 0 >> uninstall.bat
echo ^) >> uninstall.bat
echo. >> uninstall.bat
echo echo Removing POS system... >> uninstall.bat
echo. >> uninstall.bat
echo :: Stop any running POS processes >> uninstall.bat
echo taskkill /f /im python.exe ^>nul 2^>^&1 >> uninstall.bat
echo. >> uninstall.bat
echo :: Remove desktop shortcuts >> uninstall.bat
echo if exist "%%USERPROFILE%%\Desktop\Coffee Shop POS.lnk" del "%%USERPROFILE%%\Desktop\Coffee Shop POS.lnk" >> uninstall.bat
echo if exist "%%USERPROFILE%%\Desktop\Coffee Shop POS.bat" del "%%USERPROFILE%%\Desktop\Coffee Shop POS.bat" >> uninstall.bat
echo. >> uninstall.bat
echo :: Remove installation directory >> uninstall.bat
echo cd /d "%%USERPROFILE%%\Desktop" >> uninstall.bat
echo if exist "CoffeeShopPOS" rmdir /s /q "CoffeeShopPOS" >> uninstall.bat
echo. >> uninstall.bat
echo echo ✓ Coffee Shop POS has been completely removed. >> uninstall.bat
echo echo. >> uninstall.bat
echo pause >> uninstall.bat
echo ✓ Uninstaller created

:: Launch the application
echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo ✓ Coffee Shop POS has been installed to: %INSTALL_DIR%
echo.
echo Desktop shortcut created:
echo - "Coffee Shop POS" (with coffee icon)
echo.
echo Default login credentials:
echo Admin Dashboard: admin / admin
echo Cashier POS: seller / seller
echo.
echo To start the system: Double-click "Coffee Shop POS" on your desktop
echo To start manually: Go to %INSTALL_DIR% and run "start_pos.bat"
echo To uninstall: Go to %INSTALL_DIR% and run "uninstall.bat"
echo.
echo The system will now start automatically...
echo.
echo Opening web browser in 3 seconds...
echo Press Ctrl+C to stop the server
echo.

:: Start the app in background and open browser
start /b call venv\Scripts\activate.bat && python app.py

:: Wait a moment for the server to start
timeout /t 3 /nobreak >nul

:: Open the browser
start http://localhost:8080

:: Wait for user to press a key to stop
echo.
echo Press any key to stop the POS system...
pause >nul

:: Stop the background process
taskkill /f /im python.exe >nul 2>&1

echo.
echo POS System stopped.
echo.
echo Installation complete! The POS system is now ready to use.
echo.
echo To start again: Double-click "Coffee Shop POS" on your desktop
echo To uninstall: Go to %INSTALL_DIR% and run "uninstall.bat"
echo.
pause