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

:: Set installation directory
set "INSTALL_DIR=%USERPROFILE%\CoffeeShopPOS"
set "CURRENT_DIR=%CD%"

echo [1/9] Creating installation directory...
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

:: Copy all files to installation directory
echo.
echo [2/9] Copying files...
xcopy "%CURRENT_DIR%\*" "%INSTALL_DIR%\" /E /I /H /Y >nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy files!
    pause
    exit /b 1
)
echo ✓ Files copied successfully

:: Change to installation directory
cd /d "%INSTALL_DIR%"

:: Check if Python is installed
echo.
echo [3/9] Checking Python installation...
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
echo [4/9] Creating virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

:: Activate virtual environment and install dependencies
echo.
echo [5/9] Installing dependencies...
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
echo [6/9] Setting up database...
python -c "
from app import app, db
from models import User, Role, Category, Product, ProductSize, ProductModifier
from werkzeug.security import generate_password_hash

with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print('✓ Database tables created')
        
        # Ensure admin user exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.password_hash = generate_password_hash('admin')
            admin.is_active = True
            admin.role = Role.ADMIN
        else:
            admin = User(username='admin', password_hash=generate_password_hash('admin'), role=Role.ADMIN, is_active=True)
            db.session.add(admin)
        
        # Ensure cashier user exists
        cashier = User.query.filter_by(username='seller').first()
        if cashier:
            cashier.password_hash = generate_password_hash('seller')
            cashier.is_active = True
            cashier.role = Role.CASHIER
        else:
            cashier = User(username='seller', password_hash=generate_password_hash('seller'), role=Role.CASHIER, is_active=True)
            db.session.add(cashier)
        
        db.session.commit()
        print('✓ Admin and cashier accounts created')
        
    except Exception as e:
        print(f'Database setup error: {e}')
        exit(1)
" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Database setup failed!
    pause
    exit /b 1
)

:: Populate sample data
echo.
echo [7/9] Adding sample data...
python populate_sample_data.py >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Failed to populate sample data, but continuing...
) else (
    echo ✓ Sample data added
)

:: Create start script in installation folder
echo.
echo [8/9] Creating start script...
echo @echo off > "%INSTALL_DIR%\start_pos.bat"
echo title Coffee Shop POS System >> "%INSTALL_DIR%\start_pos.bat"
echo color 0B >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo ======================================== >> "%INSTALL_DIR%\start_pos.bat"
echo echo    Coffee Shop POS System >> "%INSTALL_DIR%\start_pos.bat"
echo echo ======================================== >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo Starting POS System... >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo :: Check if virtual environment exists >> "%INSTALL_DIR%\start_pos.bat"
echo if not exist "venv" ( >> "%INSTALL_DIR%\start_pos.bat"
echo     echo ERROR: Virtual environment not found! >> "%INSTALL_DIR%\start_pos.bat"
echo     echo Please run install.bat first to set up the system. >> "%INSTALL_DIR%\start_pos.bat"
echo     echo. >> "%INSTALL_DIR%\start_pos.bat"
echo     pause >> "%INSTALL_DIR%\start_pos.bat"
echo     exit /b 1 >> "%INSTALL_DIR%\start_pos.bat"
echo ^) >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo :: Check if app.py exists >> "%INSTALL_DIR%\start_pos.bat"
echo if not exist "app.py" ( >> "%INSTALL_DIR%\start_pos.bat"
echo     echo ERROR: app.py not found! >> "%INSTALL_DIR%\start_pos.bat"
echo     echo Please make sure you're in the correct directory. >> "%INSTALL_DIR%\start_pos.bat"
echo     echo. >> "%INSTALL_DIR%\start_pos.bat"
echo     pause >> "%INSTALL_DIR%\start_pos.bat"
echo     exit /b 1 >> "%INSTALL_DIR%\start_pos.bat"
echo ^) >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo The system will be available at: http://localhost:8080 >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo Default login credentials: >> "%INSTALL_DIR%\start_pos.bat"
echo echo Admin: admin / admin >> "%INSTALL_DIR%\start_pos.bat"
echo echo Cashier: seller / seller >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo Opening web browser in 3 seconds... >> "%INSTALL_DIR%\start_pos.bat"
echo echo Press Ctrl+C to stop the server >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo :: Start the app in background and open browser >> "%INSTALL_DIR%\start_pos.bat"
echo start /b call venv\Scripts\activate.bat ^&^& python app.py >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo :: Wait a moment for the server to start >> "%INSTALL_DIR%\start_pos.bat"
echo timeout /t 3 /nobreak ^>nul >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo :: Open the browser >> "%INSTALL_DIR%\start_pos.bat"
echo start http://localhost:8080 >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo :: Wait for user to press a key to stop >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo Press any key to stop the POS system... >> "%INSTALL_DIR%\start_pos.bat"
echo pause ^>nul >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo :: Stop the background process >> "%INSTALL_DIR%\start_pos.bat"
echo taskkill /f /im python.exe ^>nul 2^>^&1 >> "%INSTALL_DIR%\start_pos.bat"
echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo. >> "%INSTALL_DIR%\start_pos.bat"
echo echo POS System stopped. >> "%INSTALL_DIR%\start_pos.bat"
echo ✓ Start script created

:: Create desktop shortcuts
echo.
echo [9/9] Creating desktop shortcuts...
set DESKTOP=%USERPROFILE%\Desktop

:: Main POS shortcut
echo [InternetShortcut] > "%DESKTOP%\Coffee Shop POS.url"
echo URL=http://localhost:8080 >> "%DESKTOP%\Coffee Shop POS.url"
echo IconFile=%INSTALL_DIR%\static\placeholder-coffee.svg >> "%DESKTOP%\Coffee Shop POS.url"
echo IconIndex=0 >> "%DESKTOP%\Coffee Shop POS.url"

:: Start POS shortcut
echo @echo off > "%DESKTOP%\Start Coffee Shop POS.bat"
echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\Start Coffee Shop POS.bat"
echo start_pos.bat >> "%DESKTOP%\Start Coffee Shop POS.bat"

echo ✓ Desktop shortcuts created

:: Create uninstaller
echo.
echo [10/10] Creating uninstaller...
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
echo if exist "%%USERPROFILE%%\Desktop\Coffee Shop POS.url" del "%%USERPROFILE%%\Desktop\Coffee Shop POS.url" >> uninstall.bat
echo if exist "%%USERPROFILE%%\Desktop\Start Coffee Shop POS.bat" del "%%USERPROFILE%%\Desktop\Start Coffee Shop POS.bat" >> uninstall.bat
echo. >> uninstall.bat
echo :: Remove installation directory >> uninstall.bat
echo cd /d "%%USERPROFILE%%" >> uninstall.bat
echo rmdir /s /q "%INSTALL_DIR%" >> uninstall.bat
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
echo Desktop shortcuts created:
echo - "Coffee Shop POS" (opens in browser)
echo - "Start Coffee Shop POS" (launches application)
echo.
echo Default login credentials:
echo Admin Dashboard: admin / admin
echo Cashier POS: seller / seller
echo.
echo To uninstall: Run "uninstall.bat" in the installation folder
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
echo Installation complete! The POS system is now installed in:
echo %INSTALL_DIR%
echo.
echo To start again: Double-click "Start Coffee Shop POS" on your desktop
echo To uninstall: Run "uninstall.bat" in the installation folder
echo.
pause