#!/usr/bin/env python3
"""
MUSE PyFiles - File Selection and Management Tool

MUSE_PYFILES is used to select data files from data bases.
It defines the data objects and sends them to display windows.
The display window is opened when the user selects a data file.

This is a Python/PyQt6 translation of the IDL iris_xfiles.pro application.

Usage:
    python muse_pyfiles.py

Author: Translated from IDL to Python
Original IDL version by Viggo Hansteen and Martin Wiesmann
"""

import pickle
import re
import sys
from pathlib import Path

from astropy.io import fits
from astropy.time import Time, TimeDelta
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from muse_recent_timewindows import MUSERecentTimeWindows


def get_muse_config_dir() -> Path:
    """
    Get the MUSE configuration directory.

    Creates a .muse_pyfiles directory in the user's home directory
    similar to IDL's APP_USER_DIR functionality.

    Returns
    -------
    Path
        Path to the configuration directory
    """
    config_dir = Path.home() / ".muse_pyfiles"
    config_dir.mkdir(exist_ok=True)

    # Create a README file if it doesn't exist
    readme_file = config_dir / "README.txt"
    if not readme_file.exists():
        with open(readme_file, "w") as f:
            f.write("MUSE PyFiles Configuration Directory\n")
            f.write("======================================\n\n")
            f.write("This directory contains configuration files for MUSE PyFiles.\n")
            f.write("These files can be safely deleted to reset to defaults.\n\n")
            f.write("Author: MUSE Team\n")

    return config_dir


def valid_time(time_string: str) -> bool:
    """
    Check if a time string is valid.

    Parameters
    ----------
    time_string : str
        Time string to validate

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    if not time_string or not time_string.strip():
        return False
    try:
        Time(time_string)
        return True
    except (ValueError, TypeError):
        return False


def file2time(filename: str) -> str | None:
    """
    Extract timestamp from MUSE filename.

    Assumes filename format contains a timestamp like:
    muse_*_YYYYMMDD_HHMMSS_*.fits

    Parameters
    ----------
    filename : str
        Filename to parse

    Returns
    -------
    str or None
        ISO format time string or None if not found
    """
    # Look for pattern YYYYMMDD_HHMMSS or similar
    pattern = r"(\d{8})[_T](\d{6})"
    match = re.search(pattern, filename)

    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            # Reformat: YYYYMMDD -> YYYY-MM-DD and HHMMSS -> HH:MM:SS
            formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            formatted_time = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
            dt = Time(f"{formatted_date} {formatted_time}", scale="utc")
            return dt.isot
        except ValueError:
            return None
    return None


def extract_fids(filenames: list[str]) -> tuple[list[bool], list[str]]:
    """
    Extract file IDs and determine which files have valid FIDs.

    Parameters
    ----------
    filenames : list of str
        List of filenames to check

    Returns
    -------
    fidsfound : list of bool
        Boolean array indicating which files have valid FIDs
    fids : list of str
        Extracted file IDs (empty strings for invalid)
    """
    fidsfound = []
    fids = []

    for fname in filenames:
        # Simple check - does it look like a FITS file with a timestamp?
        has_fid = bool(re.search(r"\d{8}[_T]\d{6}", fname))
        fidsfound.append(has_fid)
        fids.append(fname if has_fid else "")

    return fidsfound, fids


class MUSEXControl(QDialog):
    """
    Placeholder for MUSE XControl window.

    This is a simple window with a close button, as requested.
    In the full implementation, this would display the FITS data.
    """

    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.setWindowTitle(f"MUSE XControl - {Path(filename).name}")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()

        label = QLabel(f"File: {filename}")
        label.setWordWrap(True)
        layout.addWidget(label)

        info_label = QLabel(
            "\nThis is a placeholder window.\nFull data display functionality would go here."
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)


class MUSEPyFiles(QMainWindow):
    """
    Main MUSE PyFiles window for file selection and management.
    """

    def __init__(self):
        super().__init__()

        # Initialize data structures
        self.sdir = str(Path.home())
        self.filter = "muse_*"
        self.datatype = "MUSE"
        self.filelistall = []
        self.filelist = []
        self.file2obsmap = []
        self.OBSids = []
        self.OBSreps = []
        self.xmlfolder = str(Path.home())
        self.fileselect = ""

        # Load saved configuration
        self.load_config()

        # Initialize UI
        self.init_ui()

        # Set initial values
        self.update_search_dir()

    def load_config(self):
        """Load saved configuration from disk"""
        config_file = get_muse_config_dir() / "muse_pyfiles_searches.pkl"

        # Set defaults
        self.tstartval = "2014-06-17 18:14:05"  # MUSE first light
        self.tstopval = Time.now() + TimeDelta(1, format="jd")
        self.ignoretime = False

        # SPICE-style options
        self.top_dir_choice = 0  # 0 = env var, 1 = manual path
        self.top_dir_env_var = "MUSE_DATA"
        self.dir_manual = str(Path.home())
        self.level = 2  # Default level
        self.use_levelx = True
        self.use_tree_struct = True
        self.search_subdirs = True

        starttimes = [self.tstartval]
        endtimes = [self.tstopval]

        if config_file.exists():
            try:
                with open(config_file, "rb") as f:
                    config = pickle.load(f)
                    self.sdir = config.get("sdir", self.sdir)
                    self.tstartval = config.get("tstartval", self.tstartval)
                    self.tstopval = config.get("tstopval", self.tstopval)
                    self.ignoretime = config.get("ignoretime", self.ignoretime)
                    self.xmlfolder = config.get("xmlfolder", self.xmlfolder)

                    # Load SPICE-style options
                    self.top_dir_choice = config.get("top_dir_choice", self.top_dir_choice)
                    self.top_dir_env_var = config.get("top_dir_env_var", self.top_dir_env_var)
                    self.dir_manual = config.get("dir_manual", self.dir_manual)
                    self.level = config.get("level", self.level)
                    self.use_levelx = config.get("use_levelx", self.use_levelx)
                    self.use_tree_struct = config.get("use_tree_struct", self.use_tree_struct)
                    self.search_subdirs = config.get("search_subdirs", self.search_subdirs)

                    starttimes = config.get("starttimes", starttimes)
                    endtimes = config.get("endtimes", endtimes)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")

        # Initialize recent windows
        self.recentwindows = MUSERecentTimeWindows(starttimes, endtimes)

    def save_config(self):
        """Save configuration to disk"""
        if not valid_time(self.tstartval) or not valid_time(self.tstopval):
            return

        starttimes, endtimes = self.recentwindows.get_times()

        config = {
            "sdir": self.sdir,
            "tstartval": self.tstartval,
            "tstopval": self.tstopval,
            "ignoretime": self.ignoretime,
            "xmlfolder": self.xmlfolder,
            "top_dir_choice": self.top_dir_choice,
            "top_dir_env_var": self.top_dir_env_var,
            "dir_manual": self.dir_manual,
            "level": self.level,
            "use_levelx": self.use_levelx,
            "use_tree_struct": self.use_tree_struct,
            "search_subdirs": self.search_subdirs,
            "starttimes": starttimes,
            "endtimes": endtimes,
        }

        config_file = get_muse_config_dir() / "muse_pyfiles_searches.pkl"
        try:
            with open(config_file, "wb") as f:
                pickle.dump(config, f)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MUSE PyFiles - QL Control Window")
        self.setGeometry(200, 200, 1000, 800)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Exit button row
        exit_frame = QFrame()
        exit_frame.setFrameStyle(QFrame.Shape.Box)
        exit_layout = QHBoxLayout(exit_frame)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        exit_layout.addWidget(exit_button)
        exit_layout.addStretch()

        main_layout.addWidget(exit_frame)

        # Date/time fields
        time_frame = QFrame()
        time_frame.setFrameStyle(QFrame.Shape.Box)
        time_layout = QVBoxLayout(time_frame)

        time_label = QLabel("Start/Stop for file search. Time Format: YYYY-MM-DD HH:MM:SS")
        time_layout.addWidget(time_label)

        time_input_layout = QHBoxLayout()

        time_input_layout.addWidget(QLabel("Start Time:"))
        self.tstart_edit = QLineEdit(self.tstartval)
        time_input_layout.addWidget(self.tstart_edit)

        time_input_layout.addWidget(QLabel("Stop Time:"))
        self.tstop_edit = QLineEdit(self.tstopval)
        time_input_layout.addWidget(self.tstop_edit)

        time_layout.addLayout(time_input_layout)

        # Time buttons and recent windows
        time_buttons_layout = QHBoxLayout()

        last5days_button = QPushButton("Last 5 days")
        last5days_button.clicked.connect(self.set_last_5_days)
        time_buttons_layout.addWidget(last5days_button)

        uptonow_button = QPushButton("Up until now")
        uptonow_button.clicked.connect(self.set_up_to_now)
        time_buttons_layout.addWidget(uptonow_button)

        time_buttons_layout.addWidget(QLabel("Recent time-windows:"))
        self.recent_combo = QComboBox()
        self.recent_combo.addItems(self.recentwindows.get_windows())
        self.recent_combo.currentIndexChanged.connect(self.select_recent_window)
        time_buttons_layout.addWidget(self.recent_combo)

        self.ignore_time_cb = QCheckBox("Ignore times (only if no tree structure)")
        self.ignore_time_cb.setChecked(self.ignoretime)
        time_buttons_layout.addWidget(self.ignore_time_cb)

        time_layout.addLayout(time_buttons_layout)
        main_layout.addWidget(time_frame)

        # Search filter configuration (SPICE-style)
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.Box)
        search_layout = QVBoxLayout(search_frame)

        # Top directory selection
        top_dir_layout = QHBoxLayout()
        top_dir_layout.addWidget(QLabel("Top directory:"))

        # Radio buttons for environment variable vs path
        self.top_dir_env_rb = QRadioButton("Environment variable")
        self.top_dir_path_rb = QRadioButton("Path")

        self.top_dir_group = QButtonGroup()
        self.top_dir_group.addButton(self.top_dir_env_rb, 0)
        self.top_dir_group.addButton(self.top_dir_path_rb, 1)

        if self.top_dir_choice == 0:
            self.top_dir_env_rb.setChecked(True)
        else:
            self.top_dir_path_rb.setChecked(True)

        self.top_dir_group.buttonClicked.connect(self.update_search_dir)

        top_dir_layout.addWidget(self.top_dir_env_rb)
        top_dir_layout.addWidget(self.top_dir_path_rb)

        # Environment variable field
        self.top_dir_env_edit = QLineEdit(self.top_dir_env_var)
        self.top_dir_env_edit.setPlaceholderText("Environment variable name")
        self.top_dir_env_edit.textChanged.connect(self.update_search_dir)
        top_dir_layout.addWidget(self.top_dir_env_edit)

        search_layout.addLayout(top_dir_layout)

        # Manual path field
        dir_manual_layout = QHBoxLayout()
        dir_manual_layout.addWidget(QLabel("Manual path:"))
        self.dir_manual_edit = QLineEdit(self.dir_manual)
        self.dir_manual_edit.textChanged.connect(self.update_search_dir)
        dir_manual_layout.addWidget(self.dir_manual_edit)

        change_dir_button = QPushButton("Change")
        change_dir_button.clicked.connect(self.change_directory)
        dir_manual_layout.addWidget(change_dir_button)

        search_layout.addLayout(dir_manual_layout)

        # Level selection and path options
        level_layout = QHBoxLayout()

        level_layout.addWidget(QLabel("Data Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Level 0", "Level 1", "Level 2", "Level 3"])
        self.level_combo.setCurrentIndex(self.level)
        self.level_combo.currentIndexChanged.connect(self.on_level_changed)
        level_layout.addWidget(self.level_combo)

        # Path structure checkboxes
        self.use_levelx_cb = QCheckBox("Use levelx in path")
        self.use_levelx_cb.setChecked(self.use_levelx)
        self.use_levelx_cb.stateChanged.connect(self.update_search_dir)
        level_layout.addWidget(self.use_levelx_cb)

        self.use_tree_struct_cb = QCheckBox("Use Date-tree-structure in path")
        self.use_tree_struct_cb.setChecked(self.use_tree_struct)
        self.use_tree_struct_cb.stateChanged.connect(self.update_search_dir)
        level_layout.addWidget(self.use_tree_struct_cb)

        self.search_subdirs_cb = QCheckBox("Search subdirectories")
        self.search_subdirs_cb.setChecked(self.search_subdirs)
        self.search_subdirs_cb.stateChanged.connect(self.update_search_dir)
        level_layout.addWidget(self.search_subdirs_cb)

        search_layout.addLayout(level_layout)

        # Search directory display and start button
        search_path_layout = QHBoxLayout()
        search_path_layout.addWidget(QLabel("Search Directory:"))
        self.searchdir_edit = QLineEdit()
        self.searchdir_edit.setReadOnly(True)
        search_path_layout.addWidget(self.searchdir_edit)

        start_search_button = QPushButton("Start Search")
        start_search_button.clicked.connect(self.start_search)
        search_path_layout.addWidget(start_search_button)

        search_layout.addLayout(search_path_layout)
        main_layout.addWidget(search_frame)

        # OBS list
        obs_label = QLabel("Observations:")
        main_layout.addWidget(obs_label)

        self.obs_list = QListWidget()
        self.obs_list.setMinimumHeight(150)
        self.obs_list.currentRowChanged.connect(self.select_obs)
        main_layout.addWidget(self.obs_list)

        # Files list
        files_label = QLabel("Files:")
        main_layout.addWidget(files_label)

        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(250)
        self.files_list.itemDoubleClicked.connect(self.read_file)
        main_layout.addWidget(self.files_list)

        # Action buttons
        button_layout = QHBoxLayout()

        confirm_button = QPushButton("Confirm selection")
        confirm_button.clicked.connect(self.read_file)
        button_layout.addWidget(confirm_button)

        print_button = QPushButton("Print filename to console")
        print_button.clicked.connect(self.print_filename)
        button_layout.addWidget(print_button)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def update_search_dir(self):
        """Update the search directory field based on current options"""
        import os

        # Get top directory
        self.top_dir_choice = 0 if self.top_dir_env_rb.isChecked() else 1

        if self.top_dir_choice == 0:
            # Environment variable
            self.top_dir_env_var = self.top_dir_env_edit.text().strip()
            top_dir = os.environ.get(self.top_dir_env_var, "")
            if not top_dir:
                top_dir = "./"
        else:
            # Manual path
            self.dir_manual = self.dir_manual_edit.text().strip()
            top_dir = self.dir_manual

        # Ensure trailing separator
        if not top_dir.endswith(os.sep):
            top_dir += os.sep

        # Get current level
        self.level = self.level_combo.currentIndex()

        # Get checkbox states
        self.use_levelx = self.use_levelx_cb.isChecked()
        self.use_tree_struct = self.use_tree_struct_cb.isChecked()
        self.search_subdirs = self.search_subdirs_cb.isChecked()

        # Build search path
        self.sdir = top_dir

        # Add levelx if checked
        if self.use_levelx:
            self.sdir += f"level{self.level}{os.sep}"

        # Build filter pattern
        self.filter = f"muse_l{self.level}_*.fits"

        # Show path with tree structure placeholder
        display_path = self.sdir
        if self.use_tree_struct:
            display_path += f"yyyy{os.sep}mm{os.sep}dd{os.sep}"

        display_path += self.filter

        # Add recursive indicator
        if self.search_subdirs:
            display_path += " -r"

        self.searchdir_edit.setText(display_path)

    def on_level_changed(self, index):
        """Handle level selection change"""
        self.level = index
        self.update_search_dir()

    def change_directory(self):
        """Open directory selection dialog"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Search Directory", self.dir_manual
        )

        if directory:
            self.dir_manual = directory
            self.dir_manual_edit.setText(directory)
            self.top_dir_path_rb.setChecked(True)
            self.update_search_dir()

    def set_last_5_days(self):
        """Set time range to last 5 days"""
        end_time = Time.now()
        start_time = end_time - TimeDelta(5, format="jd")

        self.tstartval = start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.tstopval = end_time.strftime("%Y-%m-%d %H:%M:%S")

        self.tstart_edit.setText(self.tstartval)
        self.tstop_edit.setText(self.tstopval)

    def set_up_to_now(self):
        """Set stop time to now"""
        end_time = Time.now()
        self.tstopval = end_time.strftime("%Y-%m-%d %H:%M:%S")
        self.tstop_edit.setText(self.tstopval)

    def select_recent_window(self, index):
        """Select a recent time window"""
        starttimes, endtimes = self.recentwindows.get_times()
        if index < len(starttimes):
            self.tstartval = starttimes[index]
            self.tstopval = endtimes[index]
            self.tstart_edit.setText(self.tstartval)
            self.tstop_edit.setText(self.tstopval)

    def start_search(self):
        """Start searching for files"""
        # Get current time values
        self.tstartval = self.tstart_edit.text().strip()
        self.tstopval = self.tstop_edit.text().strip()

        # Validate times
        if not valid_time(self.tstartval) or not valid_time(self.tstopval):
            QMessageBox.warning(
                self,
                "Invalid Time",
                "Invalid time format(s). Please use YYYY-MM-DD HH:MM:SS",
            )
            return

        # Get current settings from UI
        self.update_search_dir()
        self.ignoretime = self.ignore_time_cb.isChecked()

        # Update recent windows (only if not ignoring time or using tree structure)
        if self.use_tree_struct or not self.ignoretime:
            self.recentwindows.newsearch(self.tstartval, self.tstopval)
            self.recent_combo.clear()
            self.recent_combo.addItems(self.recentwindows.get_windows())

        # Save config
        self.save_config()

        # Perform search
        self.search_directory()

    def search_directory(self):
        """Search for files in the directory"""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            # Get search path - use the base directory without tree structure
            search_path = Path(self.sdir)
            if not search_path.exists():
                QMessageBox.warning(self, "Invalid Path", f"Directory does not exist: {self.sdir}")
                return

            # Parse times
            start_time = Time(self.tstartval, scale="utc")
            stop_time = Time(self.tstopval, scale="utc")

            # Search for files based on tree structure option
            files = []

            if self.use_tree_struct and not self.ignoretime:
                # Search in date-tree structure yyyy/mm/dd/
                # Generate date range
                dt = Time(self.tstartval, scale="utc")
                end_dt = Time(self.tstopval, scale="utc")

                current_dt = dt
                while current_dt <= end_dt:
                    date_path = (
                        search_path
                        / current_dt.strftime("%Y")
                        / current_dt.strftime("%m")
                        / current_dt.strftime("%d")
                    )
                    if date_path.exists():
                        date_files = list(date_path.glob(self.filter))
                        files.extend([str(f) for f in date_files if f.is_file()])
                    current_dt += TimeDelta(1, format="jd")
            elif self.search_subdirs:
                # Recursive search
                files = list(search_path.rglob(self.filter))
                files = [str(f) for f in files if f.is_file()]
            else:
                # Non-recursive search
                files = list(search_path.glob(self.filter))
                files = [str(f) for f in files if f.is_file()]

            # Filter by time if not ignoring
            if not self.ignoretime:
                filtered_files = []
                for f in files:
                    ftime = file2time(Path(f).name)
                    if ftime:
                        try:
                            ft = Time(ftime, scale="utc")
                            if start_time <= ft <= stop_time:
                                filtered_files.append(f)
                        except (ValueError, OSError):
                            pass
                files = filtered_files

            self.filelistall = sorted(files)

            # Extract OBS information from FITS files
            self.extract_obs_info()

        finally:
            QApplication.restoreOverrideCursor()

    def extract_obs_info(self):
        """Extract OBS information from FITS headers"""
        fits_files = [f for f in self.filelistall if f.endswith(".fits")]

        if not fits_files:
            self.obs_list.clear()
            self.files_list.clear()
            self.files_list.addItems(self.filelistall)
            self.filelist = self.filelistall.copy()
            return

        # Group files by date
        file_dates = []
        for f in fits_files:
            ftime = file2time(Path(f).name)
            if ftime:
                file_dates.append(ftime[:10])  # Just the date part
            else:
                file_dates.append("")

        unique_dates = sorted({d for d in file_dates if d})

        # Read headers for unique dates
        obs_info = []
        obs_ids = []
        obs_reps = []

        for date in unique_dates:
            # Find first file for this date
            idx = file_dates.index(date)
            try:
                with fits.open(fits_files[idx]) as hdul:
                    header = hdul[0].header

                    startobs = header.get("STARTOBS", header.get("DATE-OBS", date))
                    obsid = header.get("OBSID", "Unknown")
                    obs_desc = header.get("OBS_DESC", header.get("OBS_DEC", "No description"))
                    xcen = header.get("XCEN", 0.0)
                    ycen = header.get("YCEN", 0.0)
                    sat_rot = header.get("SAT_ROT", 0.0)
                    obsrep = header.get("OBSREP", 0)

                    obs_str = f"{startobs:20s} {obsid:15s} {obs_desc:40s} {xcen:7.1f} {ycen:7.1f} {sat_rot:7.1f}"
                    obs_info.append(obs_str)
                    obs_ids.append(obsid)
                    obs_reps.append(obsrep)
            except Exception as e:
                print(f"Warning: Could not read header from {fits_files[idx]}: {e}")

        # Update OBS list
        self.obs_list.clear()
        if obs_info:
            header = f"{'STARTOBS':20s} {'OBSID':15s} {'OBS_DESC':40s} {'XCEN':>7s} {'YCEN':>7s} {'SAT_ROT':>7s}"
            self.obs_list.addItem(header)
            self.obs_list.addItems(obs_info)

        self.OBSids = obs_ids
        self.OBSreps = obs_reps

        # Map files to OBS
        self.file2obsmap = [-1] * len(self.filelistall)

        for i, f in enumerate(self.filelistall):
            ftime = file2time(Path(f).name)
            if ftime:
                fdate = ftime[:10]
                if fdate in unique_dates:
                    obs_idx = unique_dates.index(fdate)
                    self.file2obsmap[i] = obs_idx + 1  # +1 because of header row

        # Select first OBS if available
        if len(obs_info) > 0:
            self.obs_list.setCurrentRow(1)  # Select first OBS (not header)

    def select_obs(self, row):
        """Handle OBS selection"""
        if row <= 0:  # Header or nothing selected
            self.filelist = []
            self.files_list.clear()
            return

        # Find files for this OBS
        matching_files = [
            self.filelistall[i] for i, obs_idx in enumerate(self.file2obsmap) if obs_idx == row
        ]

        self.filelist = matching_files
        self.files_list.clear()
        self.files_list.addItems([Path(f).name for f in matching_files])

    def print_filename(self):
        """Print selected filename to console"""
        if self.fileselect:
            print(self.fileselect)
        else:
            current_row = self.files_list.currentRow()
            if current_row >= 0 and current_row < len(self.filelist):
                print(self.filelist[current_row])

    def read_file(self):
        """Read and display the selected file"""
        current_row = self.files_list.currentRow()

        if current_row < 0 or current_row >= len(self.filelist):
            QMessageBox.warning(self, "No Selection", "Please select a file first.")
            return

        self.fileselect = self.filelist[current_row]

        # Check if it's a FITS file
        if not self.fileselect.endswith(".fits"):
            QMessageBox.information(
                self,
                "Not a FITS file",
                f"File: {self.fileselect}\n\nOnly FITS files can be opened.",
            )
            return

        # Open MUSE XControl window
        try:
            xcontrol = MUSEXControl(self.fileselect, self)
            xcontrol.exec()
        except (OSError, RuntimeError) as e:
            QMessageBox.critical(self, "Error", f"Error opening file:\n{e!s}")

    def closeEvent(self, event):
        """Handle window close event"""
        self.save_config()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("MUSE PyFiles")
    app.setOrganizationName("MUSE")

    # Create and show main window
    window = MUSEPyFiles()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
