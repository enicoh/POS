# How to Install Coffee Shop POS on Another PC

## Prerequisites

- **Windows PC** (Windows 10 or 11 recommended)
- **Internet Connection** (required only during installation to download Python/dependencies)

---

## Method 1: Automatic Installation (Recommended)

This uses the built-in installer to set up everything for you automatically.

**Step 1: Transfer Files**

1. Copy the entire `POS` folder (containing `Install_CoffeeShopPOS.bat`, `app.py`, etc.) to a USB drive or cloud storage.
2. Paste the folder onto the Desktop (or Documents) of the new PC.

**Step 2: Run Installer**

1. Open the folder on the new PC.
2. Double-click **`Install_CoffeeShopPOS.bat`**.
3. Click **"Install Coffee Shop POS"**.

**What the installer does for you:**

- Checks if Python is installed (and helps you install it if missing).
- Creates a dedicated folder (usually `C:\Users\YourName\Desktop\CoffeeShopPOS`).
- **Installs all dependencies** automatically.
- Sets up the database.
- Creates a desktop shortcut.

---

## Method 2: Manual Installation (For Developers)

If you prefer to install it manually or want to know exactly how to **install dependencies**, follow these steps.

**Step 1: Install Python**

- Download and install Python 3.11+ from [python.org](https://www.python.org/downloads/).
- **IMPORTANT**: Check the box **"Add Python to PATH"** during installation.

**Step 2: Create Virtual Environment**
Open Command Prompt (cmd) in the POS folder and run:

```cmd
python -m venv venv
```

**Step 3: Activate Environment**

```cmd
venv\Scripts\activate
```

_(You will see `(venv)` appear at the start of the command line)_

**Step 4: Install Dependencies**
This is the command to install all required libraries:

```cmd
pip install -r requirements.txt
```

**Step 5: Setup Database**

```cmd
python setup_database.py
python populate_sample_data.py
```

**Step 6: Run the App**

```cmd
python app.py
```

Open your browser to `http://127.0.0.1:8080`.

---

## Troubleshooting

- **Python not found?**
  Make sure you restarted your computer after installing Python, and that "Add to PATH" was checked.

- **Dependencies failed?**
  Try upgrading pip first:
  ```cmd
  python -m pip install --upgrade pip
  ```
