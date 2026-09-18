"""
MUSE_XCONTROL - Main quicklook control window.

Python/PyQt6 translation of iris_xcontrol.pro (IRIS-Software-UIO).

Usage
-----
    from muse_data import MuseData
    from muse_xcontrol import muse_xcontrol

    app = QApplication(sys.argv)
    data = MuseData()
    window = muse_xcontrol(data)
    sys.exit(app.exec())

The ``cw_bgroup`` IDL widget is replaced by ``QButtonGroup``:
  - ``/nonexclusive`` (checkbox group) ? ``QButtonGroup(exclusive=False)`` + ``QCheckBox``
  - exclusive (radio group, default)   ? ``QButtonGroup(exclusive=True)``  + ``QRadioButton``

Only three buttons are fully implemented:
  - **Display header**          ? opens a scrollable header text window
  - **Close**                   ? closes the control window
  - **Print filename to console** ? prints the data filename to stdout

All other buttons are present but do nothing.
"""

from __future__ import annotations

import sys
from typing import Optional

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from muse_data import MuseData


class MuseXControl(QMainWindow):
    """
    Main MUSE quicklook control window.

    Parameters
    ----------
    data : MuseData
        Data object providing observation metadata and array access.
    parent : QWidget, optional
        Parent widget (e.g. the file browser window).
    """

    def __init__(self, data: MuseData, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.data = data
        self.setWindowTitle(f"MUSE_Xcontrol  ?  {data.getfilename()}")
        self._setup_menu()
        self._setup_ui()
        self._populate_data_info()

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("Close", self.close)

        opt_menu = menubar.addMenu("Options")
        opt_menu.addAction("Display header", self._display_header)

    # ------------------------------------------------------------------
    # Main layout (three columns)
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        # Wrap three columns in a scroll area so the window stays usable
        # on small screens.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        scroll.setWidget(inner)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        row = QHBoxLayout(inner)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)

        lcol_frame = QFrame()
        lcol_frame.setFrameShape(QFrame.Shape.StyledPanel)
        lcol_frame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        mcol_frame = QFrame()
        mcol_frame.setFrameShape(QFrame.Shape.StyledPanel)
        mcol_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        rcol_frame = QFrame()
        rcol_frame.setFrameShape(QFrame.Shape.StyledPanel)
        rcol_frame.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        row.addWidget(lcol_frame)
        row.addWidget(mcol_frame)
        row.addWidget(rcol_frame)

        self._build_left_column(lcol_frame)
        self._build_middle_column(mcol_frame)
        self._build_right_column(rcol_frame)

    # ------------------------------------------------------------------
    # Left column
    # ------------------------------------------------------------------

    def _build_left_column(self, parent: QFrame) -> None:
        data = self.data
        nwin = data.getnwin()
        line_ids = data.getline_id()
        regions = data.getregion()
        nraster = data.getnraster()

        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ---- Line window selection ----
        linesel_box = QGroupBox("Select Line Window(s)")
        linesel_layout = QVBoxLayout(linesel_box)

        # FUV and NUV checkboxes live in a horizontal sub-row.
        # QButtonGroup with exclusive=False is the cw_bgroup /nonexclusive equivalent.
        lines_row = QHBoxLayout()
        self.line_btn_group = QButtonGroup(self)
        self.line_btn_group.setExclusive(False)

        fuv_box = QGroupBox("FUV")
        fuv_layout = QVBoxLayout(fuv_box)
        fuv_has_lines = False

        nuv_box = QGroupBox("NUV")
        nuv_layout = QVBoxLayout(nuv_box)
        nuv_has_lines = False

        for i in range(nwin):
            cb = QCheckBox(line_ids[i])
            self.line_btn_group.addButton(cb, i)
            if regions[i] == "FUV":
                fuv_layout.addWidget(cb)
                fuv_has_lines = True
            else:
                nuv_layout.addWidget(cb)
                nuv_has_lines = True

        if fuv_has_lines:
            lines_row.addWidget(fuv_box)
        if nuv_has_lines:
            lines_row.addWidget(nuv_box)

        linesel_layout.addLayout(lines_row)

        # SJI reference channel drop-down (stub ? no action)
        sji_ids = data.getsji_id()
        if sji_ids:
            sji_row = QHBoxLayout()
            sji_row.addWidget(QLabel("Level 3 ref cube:"))
            self.sji_combo = QComboBox()
            self.sji_combo.addItems(sji_ids)
            sji_row.addWidget(self.sji_combo)
            linesel_layout.addLayout(sji_row)

        # Generate level3 button (stub)
        level3_btn = QPushButton("Generate level3 files")
        level3_btn.clicked.connect(lambda: None)
        linesel_layout.addWidget(level3_btn)

        # Replace level3 checkbox (stub) ? single-item QButtonGroup /nonexclusive
        replace_group = QButtonGroup(self)
        replace_group.setExclusive(False)
        self.replace_l3_cb = QCheckBox("Replace existing level3 file")
        replace_group.addButton(self.replace_l3_cb, 0)
        linesel_layout.addWidget(self.replace_l3_cb)

        layout.addWidget(linesel_box)

        # ---- Display mode selection ----
        # cw_bgroup without /nonexclusive ? exclusive, i.e. QRadioButton group
        mode_box = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_box)

        modes = ["Detector", "Browser", "Spectroheliogram", "Whisker", "Intensity map"]
        if int(np.max(nraster)) <= 1:
            modes = modes[:3]

        self.disp_btn_group = QButtonGroup(self)  # exclusive by default

        for i, mode_name in enumerate(modes):
            rb = QRadioButton(mode_name)
            self.disp_btn_group.addButton(rb, i)
            mode_layout.addWidget(rb)

        layout.addWidget(mode_box)

        # ---- Pointing icon placeholder ----
        pointing_lbl = QLabel("[ Pointing ]")
        pointing_lbl.setFixedSize(200, 200)
        pointing_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pointing_lbl.setStyleSheet("background: black; color: white; border: 1px solid #555;")
        layout.addWidget(pointing_lbl)

        # ---- Line-fit drop-down (stub) ----
        fit_frame = QFrame()
        fit_frame.setFrameShape(QFrame.Shape.StyledPanel)
        fit_layout = QHBoxLayout(fit_frame)
        fit_layout.addWidget(QLabel("Line fit"))
        self.mom_combo = QComboBox()
        self.mom_combo.addItems(
            ["Not Selected", "Profile Moments", "Single Gauss. Fit", "Double Gauss. Fit"]
        )
        fit_layout.addWidget(self.mom_combo)
        layout.addWidget(fit_frame)

        # ---- Display header / Close buttons ----
        hdr_close_frame = QFrame()
        hdr_close_frame.setFrameShape(QFrame.Shape.StyledPanel)
        hdr_close_layout = QHBoxLayout(hdr_close_frame)

        hdr_btn = QPushButton("Display header")
        hdr_btn.clicked.connect(self._display_header)
        hdr_close_layout.addWidget(hdr_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        hdr_close_layout.addWidget(close_btn)

        layout.addWidget(hdr_close_frame)

        # ---- Print filename button ----
        print_btn = QPushButton("Print filename to console")
        print_btn.clicked.connect(self._print_filename)
        layout.addWidget(print_btn)

    # ------------------------------------------------------------------
    # Middle column
    # ------------------------------------------------------------------

    def _build_middle_column(self, parent: QFrame) -> None:
        data = self.data
        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Data information text widget
        self.data_info_text = QTextEdit()
        self.data_info_text.setReadOnly(True)
        self.data_info_text.setFont(QFont("Courier", 10))
        self.data_info_text.setMinimumWidth(480)
        self.data_info_text.setFixedHeight(280)
        layout.addWidget(self.data_info_text)

        # NUV detector icon placeholder
        nuv_title = QLabel("NUV Detector")
        nuv_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(nuv_title)

        nuv_icon = QLabel("[ NUV Detector View ]")
        nuv_icon.setFixedSize(400, 150)
        nuv_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nuv_icon.setStyleSheet("background: #111111; color: #cccccc; border: 1px solid #555;")
        layout.addWidget(nuv_icon)

        # FUV detector icon placeholder
        fuv_title = QLabel("FUV Detector")
        fuv_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(fuv_title)

        fuv_icon = QLabel("[ FUV Detector View ]")
        fuv_icon.setFixedSize(400, 150)
        fuv_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fuv_icon.setStyleSheet("background: #111111; color: #cccccc; border: 1px solid #555;")
        layout.addWidget(fuv_icon)

        # Observation metadata labels
        xcen = float(np.atleast_1d(data.getxcen())[0])
        ycen = float(np.atleast_1d(data.getycen())[0])
        fovx = float(np.atleast_1d(data.getfovx())[0])
        fovy = float(np.max(np.atleast_1d(data.getfovy())))

        obs_info_lines = [
            f"DATE_OBS: {data.getinfo('DATE_OBS')}",
            (f"XCEN: {xcen:.2f}  YCEN: {ycen:.2f}  FOVX: {fovx:.2f}  max(FOVY): {fovy:.2f}"),
            f"SAT_ROT: {float(data.getinfo('SAT_ROT')):.2f}",
            f"OBS_DESC: {data.getinfo('OBS_DESC')}",
            f"OBSLABEL: {data.getinfo('OBSLABEL')}  OBSTITLE: {data.getinfo('OBSTITLE')}",
        ]
        for text in obs_info_lines:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(lbl)

    # ------------------------------------------------------------------
    # Right column
    # ------------------------------------------------------------------

    def _build_right_column(self, parent: QFrame) -> None:
        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        sji_names = ["SJI_1330", "SJI_1400", "SJI_2796", "SJI_2832"]
        for name in sji_names:
            lbl = QLabel(f"[ {name} ]")
            lbl.setFixedSize(150, 150)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background: #111111; color: #cccccc; border: 1px solid #555;")
            layout.addWidget(lbl)

        # MUSE icon placeholder
        muse_icon = QLabel("MUSE")
        muse_icon.setFixedSize(150, 109)
        muse_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        muse_icon.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        muse_icon.setStyleSheet("background: navy; color: white; border: 1px solid #555;")
        layout.addWidget(muse_icon)

    # ------------------------------------------------------------------
    # Data info text
    # ------------------------------------------------------------------

    def _populate_data_info(self) -> None:
        """Fill the data-info text widget with observation summary."""
        data = self.data
        nwin = data.getnwin()
        nraster = data.getnraster()
        nraster_val = int(np.max(np.atleast_1d(nraster)))

        lines = [
            f"OBSID: {data.getobsid()}",
            "=" * 58,
            f"Number of raster positions: {nraster_val}",
            f"Number of line windows    : {nwin}",
            f"{'Line ID':<20}{'Wavelength':>14}   {'Width/Height':>12}",
            f"{'':20}{'(AA / pixel)':>14}   {'(pixels)':>12}",
            "=" * 58,
        ]
        for i in range(nwin):
            lid = str(data.getline_id(i))
            wvl_aa = data.getline_wvl(i, wscale="AA")
            wvl_px = data.getline_wvl(i, wscale="pixels")
            npx = data.getxw(i)
            npy = data.getyw(i)
            lines.append(f"{lid:<20}{wvl_aa:>8.1f} / {wvl_px:>5.1f}   {npx:>5} / {npy}")

        self.data_info_text.setPlainText("\n".join(lines))

    # ------------------------------------------------------------------
    # Button actions (implemented)
    # ------------------------------------------------------------------

    def _display_header(self) -> None:
        """Open a scrollable window showing the FITS headers."""
        hdr_win = QDialog(self)
        hdr_win.setWindowTitle("Header Contents")
        hdr_win.resize(820, 600)

        layout = QVBoxLayout(hdr_win)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(hdr_win.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Courier", 10))
        layout.addWidget(text_edit)

        data = self.data
        nwin = data.getnwin()
        parts = []

        for line in data.gethdr(0):
            parts.append(line)

        for iext in range(1, nwin + 1):
            parts.append(
                f"\n======= Header for extension {iext:2d} ================================"
            )
            for line in data.gethdr(iext):
                parts.append(line)

        text_edit.setPlainText("\n".join(parts))
        text_edit.moveCursor(text_edit.textCursor().MoveOperation.Start)

        hdr_win.exec()

    def _print_filename(self) -> None:
        """Print the data filename to stdout."""
        print(self.data.getfilename())


# ------------------------------------------------------------------
# Public factory function
# ------------------------------------------------------------------


def muse_xcontrol(data: MuseData, parent: Optional[QWidget] = None) -> MuseXControl:
    """
    Create and show the MUSE quicklook control window.

    Parameters
    ----------
    data : MuseData
        Data object passed to the window.
    parent : QWidget, optional
        Parent widget.

    Returns
    -------
    MuseXControl
        The created (and shown) control window.
    """
    ctrl = MuseXControl(data, parent)
    ctrl.show()
    return ctrl


# ------------------------------------------------------------------
# Standalone entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = MuseData()
    window = muse_xcontrol(data)
    sys.exit(app.exec())
