# MUSE PyFiles

Python/PyQt6 translation of the IDL `iris_xfiles.pro` application for MUSE data file selection and management.

## Overview

MUSE PyFiles is a GUI application for:
- Browsing and searching MUSE FITS data files
- Filtering files by date/time ranges
- Organizing observations (OBS)
- Opening and displaying FITS files

This is a direct translation from the original IDL code (`iris_xfiles.pro` and `iris_recent_timewindows__define.pro`), with all `iris_` prefixes changed to `muse_`.

## Installation

### Requirements

- Python 3.8 or higher
- PyQt6
- astropy
- numpy

### Quick Setup with Virtual Environment (Recommended)

The easiest way to set up the project is using one of these methods:

#### Method 1: Using the setup script

```bash
cd /Users/mawiesma/muse/MUSE-quicklook
./setup_venv.sh
```

#### Method 2: Using Make

```bash
cd /Users/mawiesma/muse/MUSE-quicklook
make install
```

Both methods will:
1. Create a Python virtual environment in `./venv`
2. Install all required dependencies
3. Install the project in editable mode

To activate the virtual environment later:

```bash
source venv/bin/activate
```

To deactivate when done:

```bash
deactivate
```

For more Make commands, run `make help`.

### Manual Installation

If you prefer to install manually:

#### Option 1: Using pyproject.toml (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the project
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

#### Option 2: Using requirements.txt

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Option 3: Global Installation

```bash
pip install PyQt6 astropy numpy python-dateutil
```

**Note:** Using a virtual environment is strongly recommended to avoid conflicts with system packages.

## Usage

### Running the Application

**If using virtual environment, activate it first:**

```bash
source venv/bin/activate
```

**Then run the application:**

```bash
# Method 1: Direct execution
python muse_pyfiles.py

# Method 2: Make it executable and run
chmod +x muse_pyfiles.py
./muse_pyfiles.py

# Method 3: Using the installed command (if installed with pip install -e .)
muse-pyfiles
```

### Main Features

#### 1. Time Range Selection

- **Start/Stop Time**: Enter time ranges in format `YYYY-MM-DD HH:MM:SS`
- **Quick Buttons**:
  - "Last 5 days": Sets start time to 5 days ago
  - "Up until now": Sets stop time to current time
- **Recent Windows**: Dropdown showing recently used time ranges

#### 2. Search Patterns

- **Free search**: Manual directory specification
- **Custom patterns**: Can be added via the Edit button
- Search patterns can use tree structures and subdirectories

#### 3. File Search

- **Search Filter**: Wildcard pattern (default: `muse_*`)
- **Search Directory**: Path to search for files
- **Start Search**: Execute the search with current parameters
- **Ignore times**: Option to search all files regardless of timestamp

#### 4. Results Display

- **Observations List**: Shows unique observations found in FITS headers
  - Displays: STARTOBS, OBSID, Description, coordinates
- **Files List**: Files belonging to selected observation
  - Double-click to open a file

#### 5. File Operations

- **Confirm selection**: Open selected file in viewer
- **Print filename**: Print full path to console

## File Structure

```
muse_pyfiles.py              # Main GUI application
muse_recent_timewindows.py   # Time window management class
test_muse_pyfiles.py         # Test suite and examples
pyproject.toml               # Modern Python project configuration
requirements.txt             # Python dependencies (legacy support)
setup_venv.sh                # Virtual environment setup script
.gitignore                   # Git ignore patterns
README_MUSE_PyFiles.md       # This file
venv/                        # Virtual environment (created by setup)
```

## Configuration

Configuration is automatically saved to `~/.muse_pyfiles/`:

- `muse_pyfiles_searches.pkl`: Saved search parameters and settings
- `README.txt`: Info about the config directory

This directory is automatically created on first run and can be safely deleted to reset all settings to defaults.

Saved settings include:
- Last used search directory
- Last used time range
- Search patterns
- Recent time windows
- Filter patterns

## Code Translation Notes

### Changes from IDL to Python

1. **Widgets**: IDL widget system ? PyQt6
   - `widget_base` ? `QWidget`, `QFrame`
   - `widget_button` ? `QPushButton`
   - `widget_list` ? `QListWidget`
   - `widget_droplist` ? `QComboBox`
   - `cw_field` ? `QLineEdit`

2. **FITS Handling**: IDL FITS routines ? `astropy.io.fits`
   - More Pythonic interface
   - Automatic resource management with context managers

3. **Configuration**: IDL `.sav` files ? Python pickle
   - Stored in `~/.muse_pyfiles/` (similar to IDL's APP_USER_DIR)

4. **Time Handling**: IDL time routines ? `astropy.time.Time`
   - `str2utc` ? `Time(string, format='isot')`
   - `utc2str` ? `time.datetime.strftime()`

5. **File Operations**: IDL `file_search` ? Python `pathlib.Path.glob()`
   - More robust and cross-platform

6. **Naming**: All `iris_` ? `muse_`
   - Functions, variables, classes, file names

### Simplified Features

The following features from the original IDL code are simplified in this translation:

1. **MUSE XControl**: Currently a placeholder window with a close button
   - In full implementation, would display FITS data
   
2. **Pattern Editor**: Basic dialog (not fully implemented)
   - Can still manually edit search directory

3. **OBS Tables**: XML downloading feature not implemented
   - Original IDL code had `iris_xfiles_showtables`

4. **Data Types**: Only MUSE data type (vs. EIS/CCSDS, EIS/FITS, EIS/HK in original)

## Extending the Application

### Adding Full Data Display

Replace the `MUSEXControl` class with a full FITS viewer:

```python
from your_fits_viewer import FITSViewer

class MUSEXControl(QDialog):
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.viewer = FITSViewer(filename)
        # ... setup viewer UI
```

### Adding More Search Patterns

Edit the `SearchPatterns` class in `muse_pyfiles.py`:

```python
def __init__(self):
    self.names = ['free search', 'archive', 'local', 'custom']
    self.paths = ['', '/archive/muse/data/', str(Path.home()), '/custom/path/']
    self.usetree = [False, True, False, True]
    self.searchsubdir = [False, True, False, True]
    self.defaul = 1
```

### Custom Time Formats

Modify `valid_time()` and `file2time()` functions to support additional formats:

```python
def valid_time(time_string: str) -> bool:
    # Add your custom format parsing here
    try:
        datetime.strptime(time_string, '%Y%m%d_%H%M%S')
        return True
    except:
        # ... existing code
```

## Troubleshooting

### Application won't start

- Check Python version: `python --version` (needs 3.8+)
- Verify PyQt6 installation: `python -c "import PyQt6; print('OK')"`
- Check astropy: `python -c "import astropy; print('OK')"`

### Files not found

- Verify the search directory exists
- Check file filter pattern (wildcards: `*` and `?`)
- Ensure FITS files have timestamps in filename
- Try "Ignore times" checkbox if timestamp parsing fails

### Configuration not saving

- Check write permissions for `~/.muse_pyfiles/`
- Ensure times are valid before closing application

### FITS header errors

- Verify FITS files are not corrupted
- Check that required keywords exist in headers
- Application will skip files with missing/invalid headers

## Original IDL Code

This is a translation of:
- `IRIS-Software-UIO/ql/iris_xfiles.pro`
- `IRIS-Software-UIO/ql/iris_recent_timewindows__define.pro`
- `IRIS-Software-UIO/ql/irisxfiles_appreadme.pro`

Original authors:
- Viggo Hansteen (Institute of Theoretical Astrophysics, University of Oslo)
- Øivind Wikstøl
- Martin Wiesmann
- Alessandro Gardini

## License

Same as original IRIS Software (see LICENSE file in IRIS-Software-UIO directory)

## Contact

For issues with the Python translation, please report to your local MUSE support team.

For issues with the original IDL code, see the IRIS Software UIO repository.
