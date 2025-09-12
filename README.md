# Coffee Shop POS System ☕

A clean, one-click Point of Sale system for coffee shops.

## Quick Start

1. **Double-click** `install.bat` to install everything
2. **The installer will**:
   - Create a dedicated folder: `%USERPROFILE%\CoffeeShopPOS`
   - Set up everything automatically
   - Create desktop shortcuts
   - Launch the system
3. **Login** with:
   - Admin: `admin` / `admin`
   - Cashier: `seller` / `seller`

## What's Included

### Core Files (Essential)
- `app.py` - Main Flask application
- `models.py` - Database models
- `routes.py` - Authentication
- `pos_routes.py` - POS features
- `config.py` - Settings
- `populate_sample_data.py` - Sample data

### Templates & Static
- `templates/` - HTML pages (login, admin, cashier)
- `static/` - CSS, JavaScript, images, uploads

### Installer & Launcher
- `install.bat` - One-click installer
- `uninstall.bat` - Complete uninstaller

**Note**: `start_pos.bat` is created automatically during installation in the POS folder.

### Database
- `instance/database.db` - SQLite database

## Installation Process

The installer creates a clean, dedicated folder with everything needed:
- ✅ Creates `%USERPROFILE%\CoffeeShopPOS` folder
- ✅ Copies all files
- ✅ Sets up Python virtual environment
- ✅ Installs all dependencies
- ✅ Creates database and users
- ✅ Adds sample data
- ✅ Creates `start_pos.bat` launcher
- ✅ Creates desktop shortcuts
- ✅ Creates uninstaller

## Features

- **Admin Dashboard**: Manage products, users, sales
- **Cashier POS**: Process orders, payments
- **Pending Orders**: Save orders for dine-in customers
- **PDF Reports**: Generate sales reports
- **Product Images**: Upload product photos
- **Cash Calculator**: Calculate change

## Uninstalling

Run `uninstall.bat` (from anywhere) to completely remove everything.

## Requirements

- Windows 10/11
- Python 3.8+ (auto-detected)
- Internet connection (for setup)

Clean, simple, and ready to use!