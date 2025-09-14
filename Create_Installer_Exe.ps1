# Script to create a standalone executable installer
# This requires PS2EXE module to be installed

Write-Host "Coffee Shop POS - Creating Standalone Installer" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Check if PS2EXE is installed
try {
    Import-Module PS2EXE -ErrorAction Stop
    Write-Host "✓ PS2EXE module found" -ForegroundColor Green
}
catch {
    Write-Host "PS2EXE module not found. Installing..." -ForegroundColor Yellow
    try {
        Install-Module -Name PS2EXE -Force -Scope CurrentUser
        Import-Module PS2EXE
        Write-Host "✓ PS2EXE module installed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to install PS2EXE module" -ForegroundColor Red
        Write-Host "Please install manually: Install-Module -Name PS2EXE" -ForegroundColor Yellow
        Write-Host "Or use the batch file launcher instead." -ForegroundColor Yellow
        exit 1
    }
}

# Create the executable
Write-Host "Creating standalone installer executable..." -ForegroundColor Yellow

try {
    ps2exe -inputFile "CoffeeShopPOS_Installer.ps1" -outputFile "CoffeeShopPOS_Installer.exe" -iconFile "static\placeholder-coffee.svg" -title "Coffee Shop POS Installer" -description "Professional installer for Coffee Shop POS System" -company "Coffee Shop Solutions" -version "1.0.0.0" -copyright "2024" -requireAdmin:$false -supportOS:$true -longPaths:$true
    
    if (Test-Path "CoffeeShopPOS_Installer.exe") {
        Write-Host "✓ Standalone installer created successfully!" -ForegroundColor Green
        Write-Host "File: CoffeeShopPOS_Installer.exe" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "You can now distribute this single EXE file to install the POS system." -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create executable" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error creating executable: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "You can still use the batch file launcher: Install_CoffeeShopPOS.bat" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
