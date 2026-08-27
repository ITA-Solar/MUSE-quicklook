.PHONY: help install test run clean venv

# Default target
help:
	@echo "MUSE PyFiles - Available targets:"
	@echo ""
	@echo "  make install    - Set up virtual environment and install dependencies"
	@echo "  make venv       - Create virtual environment only"
	@echo "  make test       - Run test suite"
	@echo "  make run        - Run the application"
	@echo "  make clean      - Remove virtual environment and cache files"
	@echo "  make help       - Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make install"
	@echo "  2. source venv/bin/activate"
	@echo "  3. make run"

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "? Virtual environment created"
	@echo ""
	@echo "To activate, run: source venv/bin/activate"

# Install dependencies
install: venv
	@echo "Installing dependencies..."
	@bash -c "source venv/bin/activate && pip install --upgrade pip setuptools wheel"
	@bash -c "source venv/bin/activate && pip install -e ."
	@echo "? Installation complete"
	@echo ""
	@echo "To activate the environment, run: source venv/bin/activate"

# Run tests
test:
	@bash -c "source venv/bin/activate && python test_muse_pyfiles.py"

# Run application
run:
	@bash -c "source venv/bin/activate && python muse_pyfiles.py"

# Clean up
clean:
	@echo "Removing virtual environment and cache files..."
	rm -rf venv/
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	rm -rf build/
	rm -rf dist/
	@echo "? Cleanup complete"
