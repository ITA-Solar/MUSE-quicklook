#!/bin/bash
# MUSE PyFiles Virtual Environment Setup Script

set -e  # Exit on error

echo "=================================="
echo "MUSE PyFiles Environment Setup"
echo "=================================="
echo ""

# Check Python version
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at ./$VENV_DIR"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing virtual environment."
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "? Virtual environment created"
fi

echo ""
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "? Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "? pip upgraded"
echo ""

# Install project dependencies
echo "Installing project dependencies..."
if [ -f "pyproject.toml" ]; then
    pip install -e .
    echo "? Project installed in editable mode"
else
    pip install -r requirements.txt
    echo "? Dependencies installed from requirements.txt"
fi

echo ""
echo "Installing development dependencies..."
pip install -e ".[dev]" 2>/dev/null || echo "Note: Dev dependencies not available, skipping..."

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run MUSE PyFiles:"
echo "  python muse_pyfiles.py"
echo "  or: muse-pyfiles"
echo ""
echo "To run tests:"
echo "  python test_muse_pyfiles.py"
echo ""
echo "To deactivate the virtual environment when done:"
echo "  deactivate"
echo ""
