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
from datetime import datetime, timedelta
from pathlib import Path

from astropy.io import fits
from astropy.time import Time
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
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
    QVBoxLayout,
    QWidget,
)

from muse_recent_timewindows import MUSERecentTimeWindows


class SearchPatterns:
    """Structure to hold search pattern configurations"""

    def __init__(self):
        self.names = ["free search", "local"]
        self.paths = ["", str(Path.home())]
        self.usetree = [False, False]
        self.searchsubdir = [False, False]
        self.defaul = 1  # Default selection index


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
        Time(time_string, format="isot", scale="utc")
        return True
    except (ValueError, TypeError):
        # Try other common formats
        try:
            datetime.strptime(time_string, "%d-%b-%y %H:%M:%S")
            return True
        except ValueError:
            try:
                datetime.strptime(time_string, "%d-%b-%Y %H:%M:%S")
                return True
            except ValueError:
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
            dt = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
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
            "\nThis is a placeholder window.\n"
            "Full data display functionality would go here."
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
        self.tstopval = (datetime.now() + timedelta(days=1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        self.ignoretime = False
        self.spatterns = SearchPatterns()

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

                    # Load search patterns if available
                    if "spatterns" in config:
                        sp = config["spatterns"]
                        self.spatterns.names = sp.get("names", self.spatterns.names)
                        self.spatterns.paths = sp.get("paths", self.spatterns.paths)
                        self.spatterns.usetree = sp.get(
                            "usetree", self.spatterns.usetree
                        )
                        self.spatterns.searchsubdir = sp.get(
                            "searchsubdir", self.spatterns.searchsubdir
                        )
                        self.spatterns.defaul = sp.get("defaul", self.spatterns.defaul)

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
            "spatterns": {
                "names": self.spatterns.names,
                "paths": self.spatterns.paths,
                "usetree": self.spatterns.usetree,
                "searchsubdir": self.spatterns.searchsubdir,
                "defaul": self.spatterns.defaul,
            },
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

        time_label = QLabel(
            "Start/Stop for file search. Time Format: YYYY-MM-DD HH:MM:SS"
        )
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

        # Search filter and pattern
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.Box)
        search_layout = QVBoxLayout(search_frame)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Set search filter:"))
        self.filter_edit = QLineEdit(self.filter)
        filter_layout.addWidget(self.filter_edit)
        search_layout.addLayout(filter_layout)

        # Search pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Search Pattern:"))
        self.search_pattern_combo = QComboBox()
        self.search_pattern_combo.addItems(self.spatterns.names)
        self.search_pattern_combo.setCurrentIndex(self.spatterns.defaul)
        self.search_pattern_combo.currentIndexChanged.connect(self.change_pattern)
        pattern_layout.addWidget(self.search_pattern_combo)

        edit_pattern_button = QPushButton("Edit")
        edit_pattern_button.clicked.connect(self.edit_patterns)
        pattern_layout.addWidget(edit_pattern_button)

        pattern_layout.addStretch()

        start_search_button = QPushButton("Start Search")
        start_search_button.clicked.connect(self.start_search)
        pattern_layout.addWidget(start_search_button)

        search_layout.addLayout(pattern_layout)

        # Search directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Search Directory:"))
        self.searchdir_edit = QLineEdit(self.sdir)
        dir_layout.addWidget(self.searchdir_edit)

        change_dir_button = QPushButton("Change")
        change_dir_button.clicked.connect(self.change_directory)
        dir_layout.addWidget(change_dir_button)

        search_layout.addLayout(dir_layout)
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
        """Update the search directory field"""
        pattern_idx = self.search_pattern_combo.currentIndex()
        if pattern_idx < len(self.spatterns.paths):
            path = self.spatterns.paths[pattern_idx]
            if path:
                self.searchdir_edit.setText(path)
                self.sdir = path
            else:
                self.searchdir_edit.setText(self.sdir)

    def change_pattern(self, index):
        """Handle search pattern change"""
        if index < len(self.spatterns.paths):
            path = self.spatterns.paths[index]
            if path:
                self.searchdir_edit.setText(path)
                self.sdir = path

    def set_last_5_days(self):
        """Set time range to last 5 days"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=5)

        self.tstartval = start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.tstopval = end_time.strftime("%Y-%m-%d %H:%M:%S")

        self.tstart_edit.setText(self.tstartval)
        self.tstop_edit.setText(self.tstopval)

    def set_up_to_now(self):
        """Set stop time to now"""
        end_time = datetime.now()
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

    def edit_patterns(self):
        """Open pattern editor dialog (simplified version)"""
        QMessageBox.information(
            self,
            "Edit Patterns",
            "Pattern editing dialog not yet implemented.\n"
            "You can manually edit the search directory field.",
        )

    def change_directory(self):
        """Open directory selection dialog"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Search Directory", self.sdir
        )

        if directory:
            self.sdir = directory
            self.searchdir_edit.setText(directory)
            self.search_pattern_combo.setCurrentIndex(0)  # Set to 'free search'

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

        # Get current settings
        self.sdir = self.searchdir_edit.text().strip()
        self.filter = self.filter_edit.text().strip() or "*"
        self.ignoretime = self.ignore_time_cb.isChecked()

        pattern_idx = self.search_pattern_combo.currentIndex()

        # Update recent windows
        if pattern_idx < len(self.spatterns.usetree) and (
            self.spatterns.usetree[pattern_idx] or not self.ignoretime
        ):
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
            # Get search path
            search_path = Path(self.sdir)
            if not search_path.exists():
                QMessageBox.warning(
                    self, "Invalid Path", f"Directory does not exist: {self.sdir}"
                )
                return

            # Parse times
            try:
                start_time = Time(self.tstartval, format="isot", scale="utc")
                stop_time = Time(self.tstopval, format="isot", scale="utc")
            except:
                start_time = Time(
                    datetime.strptime(self.tstartval, "%Y-%m-%d %H:%M:%S")
                )
                stop_time = Time(datetime.strptime(self.tstopval, "%Y-%m-%d %H:%M:%S"))

            # Search for files
            pattern_idx = self.search_pattern_combo.currentIndex()
            search_subdir = (
                pattern_idx < len(self.spatterns.searchsubdir)
                and self.spatterns.searchsubdir[pattern_idx]
            )

            if search_subdir:
                files = list(search_path.rglob(self.filter))
            else:
                files = list(search_path.glob(self.filter))

            # Convert to strings
            files = [str(f) for f in files if f.is_file()]

            # Filter by time if not ignoring
            if not self.ignoretime:
                filtered_files = []
                for f in files:
                    ftime = file2time(Path(f).name)
                    if ftime:
                        try:
                            ft = Time(ftime, format="isot", scale="utc")
                            if start_time <= ft <= stop_time:
                                filtered_files.append(f)
                        except:
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
                    obs_desc = header.get(
                        "OBS_DESC", header.get("OBS_DEC", "No description")
                    )
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
            self.filelistall[i]
            for i, obs_idx in enumerate(self.file2obsmap)
            if obs_idx == row
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
