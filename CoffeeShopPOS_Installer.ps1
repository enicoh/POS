# Coffee Shop POS System - Professional Installer
# PowerShell GUI Installer with comprehensive error handling

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Global variables
$script:InstallDir = "$env:USERPROFILE\Desktop\CoffeeShopPOS"
$script:SourceDir = $PSScriptRoot
$script:LogFile = "$env:TEMP\CoffeeShopPOS_Install.log"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $script:LogFile -Value $logEntry
    Write-Host $logEntry
}

# Error handling
function Show-Error {
    param([string]$Message, [string]$Title = "Installation Error")
    Write-Log "ERROR: $Message" "ERROR"
    [System.Windows.Forms.MessageBox]::Show($Message, $Title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
}

# Success message
function Show-Success {
    param([string]$Message, [string]$Title = "Success")
    Write-Log "SUCCESS: $Message" "SUCCESS"
    [System.Windows.Forms.MessageBox]::Show($Message, $Title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check Python installation
function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Python found: $pythonVersion"
            return $true
        }
    }
    catch {
        Write-Log "Python not found in PATH" "WARNING"
    }
    return $false
}

# Install Python if not found
function Install-Python {
    Write-Log "Attempting to install Python..."
    
    # Check if Python is installed but not in PATH
    $pythonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
        "$env:PROGRAMFILES\Python*\python.exe",
        "$env:PROGRAMFILES(X86)\Python*\python.exe"
    )
    
    foreach ($path in $pythonPaths) {
        $foundPython = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
        if ($foundPython) {
            Write-Log "Found Python at: $($foundPython.FullName)"
            return $foundPython.FullName
        }
    }
    
    # If not found, show download message
    $result = [System.Windows.Forms.MessageBox]::Show(
        "Python is not installed or not in PATH.`n`nWould you like to download Python 3.11+ from python.org?`n`nClick Yes to open the download page, or No to cancel installation.",
        "Python Required",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    
    if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
        Start-Process "https://www.python.org/downloads/"
    }
    
    return $null
}

# Main installation function
function Install-CoffeeShopPOS {
    param([System.Windows.Forms.Form]$Form, [System.Windows.Forms.ProgressBar]$ProgressBar, [System.Windows.Forms.Label]$StatusLabel)
    
    try {
        Write-Log "Starting Coffee Shop POS installation..."
        
        # Step 1: Check Python
        $StatusLabel.Text = "Checking Python installation..."
        $ProgressBar.Value = 10
        $Form.Refresh()
        
        if (-not (Test-PythonInstallation)) {
            $pythonPath = Install-Python
            if (-not $pythonPath) {
                Show-Error "Python installation is required. Please install Python 3.8+ and try again."
                return $false
            }
        }
        
        # Step 2: Create installation directory
        $StatusLabel.Text = "Creating installation directory..."
        $ProgressBar.Value = 20
        $Form.Refresh()
        
        if (Test-Path $script:InstallDir) {
            Write-Log "Removing existing installation directory..."
            Remove-Item -Path $script:InstallDir -Recurse -Force
        }
        
        New-Item -ItemType Directory -Path $script:InstallDir -Force | Out-Null
        Write-Log "Installation directory created: $script:InstallDir"
        
        # Step 3: Copy files
        $StatusLabel.Text = "Copying application files..."
        $ProgressBar.Value = 30
        $Form.Refresh()
        
        $filesToCopy = @(
            "app.py", "config.py", "models.py", "populate_sample_data.py",
            "pos_routes.py", "routes.py", "requirements.txt", "setup_database.py"
        )
        
        foreach ($file in $filesToCopy) {
            if (Test-Path "$script:SourceDir\$file") {
                Copy-Item "$script:SourceDir\$file" "$script:InstallDir\" -Force
                Write-Log "Copied: $file"
            } else {
                Write-Log "Warning: $file not found in source directory" "WARNING"
            }
        }
        
        # Copy directories
        if (Test-Path "$script:SourceDir\static") {
            Copy-Item "$script:SourceDir\static" "$script:InstallDir\" -Recurse -Force
            Write-Log "Copied: static directory"
        }
        
        if (Test-Path "$script:SourceDir\templates") {
            Copy-Item "$script:SourceDir\templates" "$script:InstallDir\" -Recurse -Force
            Write-Log "Copied: templates directory"
        }
        
        # Step 4: Create virtual environment
        $StatusLabel.Text = "Creating virtual environment..."
        $ProgressBar.Value = 50
        $Form.Refresh()
        
        Set-Location $script:InstallDir
        
        # Use python command (should be in PATH now)
        $pythonCmd = "python"
        if ($pythonPath) {
            $pythonCmd = $pythonPath
        }
        
        & $pythonCmd -m venv venv
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment"
        }
        
        Write-Log "Virtual environment created successfully"
        
        # Step 5: Install dependencies
        $StatusLabel.Text = "Installing dependencies..."
        $ProgressBar.Value = 70
        $Form.Refresh()
        
        $activateScript = if ($IsWindows -or $env:OS -eq "Windows_NT") { "venv\Scripts\Activate.ps1" } else { "venv/bin/Activate.ps1" }
        
        # Upgrade pip
        & "$script:InstallDir\$activateScript"
        & "$script:InstallDir\venv\Scripts\python.exe" -m pip install --upgrade pip
        
        # Install requirements
        & "$script:InstallDir\venv\Scripts\python.exe" -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install dependencies"
        }
        
        Write-Log "Dependencies installed successfully"
        
        # Step 6: Setup database
        $StatusLabel.Text = "Setting up database..."
        $ProgressBar.Value = 85
        $Form.Refresh()
        
        & "$script:InstallDir\venv\Scripts\python.exe" setup_database.py
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Database setup failed, but continuing..." "WARNING"
        } else {
            Write-Log "Database setup completed"
        }
        
        # Step 7: Skip sample data (clean installation)
        $StatusLabel.Text = "Preparing clean installation..."
        $ProgressBar.Value = 90
        $Form.Refresh()
        
        Write-Log "Clean installation - no sample data will be added"
        Write-Log "Users will need to add their own products and categories"
        
        # Step 8: Create shortcuts and launcher
        $StatusLabel.Text = "Creating shortcuts..."
        $ProgressBar.Value = 95
        $Form.Refresh()
        
        # Create start script
        $startScript = @"
@echo off
title Coffee Shop POS System
color 0B
echo.
echo ========================================
echo    Coffee Shop POS System
echo ========================================
echo.
echo Starting POS System...
echo.
cd /d "$script:InstallDir"
call venv\Scripts\activate.bat
python app.py
pause
"@
        
        $startScript | Out-File -FilePath "$script:InstallDir\start_pos.bat" -Encoding ASCII
        
        # Create desktop shortcut
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Coffee Shop POS.lnk")
        $Shortcut.TargetPath = "$script:InstallDir\start_pos.bat"
        $Shortcut.WorkingDirectory = $script:InstallDir
        $Shortcut.Description = "Coffee Shop POS System"
        $Shortcut.Save()
        
        Write-Log "Desktop shortcut created"
        
        # Copy uninstaller to installation directory
        if (Test-Path "$script:SourceDir\Uninstall_CoffeeShopPOS.bat") {
            Copy-Item "$script:SourceDir\Uninstall_CoffeeShopPOS.bat" "$script:InstallDir\Uninstall_CoffeeShopPOS.bat" -Force
            Write-Log "Uninstaller copied to installation directory"
        }
        
        # Step 9: Complete
        $StatusLabel.Text = "Installation completed!"
        $ProgressBar.Value = 100
        $Form.Refresh()
        
        Write-Log "Installation completed successfully"
        return $true
        
    }
    catch {
        Write-Log "Installation failed: $($_.Exception.Message)" "ERROR"
        Show-Error "Installation failed: $($_.Exception.Message)"
        return $false
    }
    finally {
        Set-Location $script:SourceDir
    }
}

# Create the main form
function Show-InstallerGUI {
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Coffee Shop POS - Professional Installer"
    $form.Size = New-Object System.Drawing.Size(500, 400)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    
    # Set icon (if available)
    try {
        $form.Icon = [System.Drawing.SystemIcons]::Application
    }
    catch {
        # Icon not available, continue without it
    }
    
    # Title label
    $titleLabel = New-Object System.Windows.Forms.Label
    $titleLabel.Text = "Coffee Shop POS System"
    $titleLabel.Font = New-Object System.Drawing.Font("Arial", 16, [System.Drawing.FontStyle]::Bold)
    $titleLabel.Size = New-Object System.Drawing.Size(400, 30)
    $titleLabel.Location = New-Object System.Drawing.Point(50, 20)
    $titleLabel.TextAlign = "MiddleCenter"
    $form.Controls.Add($titleLabel)
    
    # Subtitle label
    $subtitleLabel = New-Object System.Windows.Forms.Label
    $subtitleLabel.Text = "Professional Point of Sale System for Coffee Shops"
    $subtitleLabel.Font = New-Object System.Drawing.Font("Arial", 10)
    $subtitleLabel.Size = New-Object System.Drawing.Size(400, 20)
    $subtitleLabel.Location = New-Object System.Drawing.Point(50, 50)
    $subtitleLabel.TextAlign = "MiddleCenter"
    $form.Controls.Add($subtitleLabel)
    
    # Installation directory label
    $dirLabel = New-Object System.Windows.Forms.Label
    $dirLabel.Text = "Installation Directory:"
    $dirLabel.Size = New-Object System.Drawing.Size(120, 20)
    $dirLabel.Location = New-Object System.Drawing.Point(20, 90)
    $form.Controls.Add($dirLabel)
    
    $dirTextBox = New-Object System.Windows.Forms.TextBox
    $dirTextBox.Text = $script:InstallDir
    $dirTextBox.Size = New-Object System.Drawing.Size(350, 20)
    $dirTextBox.Location = New-Object System.Drawing.Point(20, 110)
    $dirTextBox.ReadOnly = $true
    $form.Controls.Add($dirTextBox)
    
    # Progress bar
    $progressBar = New-Object System.Windows.Forms.ProgressBar
    $progressBar.Size = New-Object System.Drawing.Size(450, 25)
    $progressBar.Location = New-Object System.Drawing.Point(20, 150)
    $progressBar.Style = "Continuous"
    $form.Controls.Add($progressBar)
    
    # Status label
    $statusLabel = New-Object System.Windows.Forms.Label
    $statusLabel.Text = "Ready to install..."
    $statusLabel.Size = New-Object System.Drawing.Size(450, 20)
    $statusLabel.Location = New-Object System.Drawing.Point(20, 180)
    $form.Controls.Add($statusLabel)
    
    # Features list
    $featuresLabel = New-Object System.Windows.Forms.Label
    $featuresLabel.Text = "Features:"
    $featuresLabel.Font = New-Object System.Drawing.Font("Arial", 10, [System.Drawing.FontStyle]::Bold)
    $featuresLabel.Size = New-Object System.Drawing.Size(100, 20)
    $featuresLabel.Location = New-Object System.Drawing.Point(20, 210)
    $form.Controls.Add($featuresLabel)
    
    $featuresList = New-Object System.Windows.Forms.Label
    $featuresList.Text = "• Admin Dashboard`n• Cashier POS Interface`n• Order Management`n• PDF Reports`n• Product Images`n• One-Click Installation"
    $featuresList.Size = New-Object System.Drawing.Size(450, 80)
    $featuresList.Location = New-Object System.Drawing.Point(20, 230)
    $form.Controls.Add($featuresList)
    
    # Install button
    $installButton = New-Object System.Windows.Forms.Button
    $installButton.Text = "Install Coffee Shop POS"
    $installButton.Size = New-Object System.Drawing.Size(150, 35)
    $installButton.Location = New-Object System.Drawing.Point(20, 320)
    $installButton.Font = New-Object System.Drawing.Font("Arial", 10, [System.Drawing.FontStyle]::Bold)
    $installButton.BackColor = [System.Drawing.Color]::LightGreen
    $form.Controls.Add($installButton)
    
    # Cancel button
    $cancelButton = New-Object System.Windows.Forms.Button
    $cancelButton.Text = "Cancel"
    $cancelButton.Size = New-Object System.Drawing.Size(100, 35)
    $cancelButton.Location = New-Object System.Drawing.Point(180, 320)
    $form.Controls.Add($cancelButton)
    
    # Exit button
    $exitButton = New-Object System.Windows.Forms.Button
    $exitButton.Text = "Exit"
    $exitButton.Size = New-Object System.Drawing.Size(100, 35)
    $exitButton.Location = New-Object System.Drawing.Point(290, 320)
    $form.Controls.Add($exitButton)
    
    # Event handlers
    $installButton.Add_Click({
        $installButton.Enabled = $false
        $cancelButton.Enabled = $false
        $exitButton.Enabled = $false
        
        $success = Install-CoffeeShopPOS -Form $form -ProgressBar $progressBar -StatusLabel $statusLabel
        
        if ($success) {
            $result = [System.Windows.Forms.MessageBox]::Show(
                "Installation completed successfully!`n`nThe Coffee Shop POS system has been installed to:`n$script:InstallDir`n`nA desktop shortcut has been created.`n`nIMPORTANT: This is a clean installation with no sample data.`nYou will need to add your own products and categories.`n`nDefault login credentials:`nAdmin: admin / admin`nCashier: seller / seller`n`nTo uninstall: Run Uninstall_CoffeeShopPOS.bat in the installation folder`n`nWould you like to start the POS system now?",
                "Installation Complete",
                [System.Windows.Forms.MessageBoxButtons]::YesNo,
                [System.Windows.Forms.MessageBoxIcon]::Information
            )
            
            if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
                Start-Process "$script:InstallDir\start_pos.bat"
            }
        }
        
        $installButton.Enabled = $true
        $cancelButton.Enabled = $true
        $exitButton.Enabled = $true
    })
    
    $cancelButton.Add_Click({
        $form.Close()
    })
    
    $exitButton.Add_Click({
        $form.Close()
    })
    
    # Show the form
    $form.Add_Shown({$form.Activate()})
    $form.ShowDialog() | Out-Null
}

# Main execution
Write-Log "Coffee Shop POS Installer started"

# Check if running as administrator (optional)
if (-not (Test-Administrator)) {
    Write-Log "Not running as administrator (this is usually fine for user installations)"
}

# Show the installer GUI
Show-InstallerGUI

Write-Log "Coffee Shop POS Installer finished"
