# MUSE PyFiles Installation Guide

## Quick Start

### 1. Automated Setup (Recommended)

Run the setup script to automatically create a virtual environment and install all dependencies:

```bash
cd /Users/mawiesma/muse/MUSE-quicklook
./setup_venv.sh
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Run the Application

```bash
python muse_pyfiles.py
# or
muse-pyfiles
```

---

## Detailed Installation Steps

### Prerequisites

- **Python 3.8 or higher** - Check with: `python3 --version`
- **pip** - Usually comes with Python

### Method 1: Using setup script (Easiest)

```bash
# Navigate to project directory
cd /Users/mawiesma/muse/MUSE-quicklook

# Run setup script
./setup_venv.sh

# Activate virtual environment
source venv/bin/activate

# Run application
python muse_pyfiles.py
```

### Method 2: Manual setup with pyproject.toml

```bash
# Navigate to project directory
cd /Users/mawiesma/muse/MUSE-quicklook

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install project in editable mode
pip install -e .

# Run application
muse-pyfiles
```

### Method 3: Manual setup with requirements.txt

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run application
python muse_pyfiles.py
```

---

## Verifying Installation

Run the test suite to verify everything is working:

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run tests
python test_muse_pyfiles.py
```

You should see output like:
```
==================================
MUSE PyFiles Module Tests
==================================
...
ALL TESTS PASSED! ?
```

---

## Running the Application

### Option 1: Python script

```bash
source venv/bin/activate
python muse_pyfiles.py
```

### Option 2: Installed command (after `pip install -e .`)

```bash
source venv/bin/activate
muse-pyfiles
```

### Option 3: Direct execution

```bash
source venv/bin/activate
./muse_pyfiles.py
```

---

## Troubleshooting

### "python3: command not found"

Install Python from [python.org](https://www.python.org/downloads/) or use your system package manager:

- **macOS**: `brew install python3`
- **Ubuntu/Debian**: `sudo apt-get install python3 python3-venv`
- **Windows**: Download from python.org

### "ModuleNotFoundError: No module named 'PyQt6'"

Make sure the virtual environment is activated:

```bash
source venv/bin/activate
```

Then reinstall dependencies:

```bash
pip install -r requirements.txt
```

### "Permission denied" when running setup_venv.sh

Make the script executable:

```bash
chmod +x setup_venv.sh
```

### Application won't start

1. Check Python version: `python3 --version` (needs 3.8+)
2. Activate virtual environment: `source venv/bin/activate`
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Check for errors: `python -c "import PyQt6; import astropy; print('OK')"`

---

## Deactivating the Virtual Environment

When you're done working with MUSE PyFiles:

```bash
deactivate
```

---

## Uninstalling

To completely remove MUSE PyFiles:

```bash
# Remove virtual environment
rm -rf venv/

# Remove configuration (optional)
rm -rf ~/.muse_pyfiles/
```

---

## Development Installation

For development with additional tools (pytest, black, ruff):

```bash
source venv/bin/activate
pip install -e ".[dev]"
```

---

For more detailed information, see [README_MUSE_PyFiles.md](README_MUSE_PyFiles.md).
