"""
MuseData - Generic MUSE data object with plausible mock data.

Python equivalent of the IDL iris_data object used in iris_xcontrol / muse_xcontrol.
All methods return representative values for a multi-window spectral raster
observation so that muse_xcontrol can run without real FITS files.
"""

from __future__ import annotations

from typing import List, Optional, Union

import numpy as np


class MuseData:
    """
    Generic MUSE data object.

    Provides the same interface as the IDL iris_data object used in
    iris_xcontrol.pro, returning plausible generic values instead of
    reading real FITS files.

    Parameters
    ----------
    filename : str
        Logical filename reported by :meth:`getfilename`.
    """

    # --- class-level mock catalogue ---

    _LINE_IDS: List[str] = [
        "C II 1336",
        "Si IV 1394",
        "Mg II k 2796",
        "Mg II h 2803",
    ]
    _LINE_WVL_AA: List[float] = [1335.71, 1393.76, 2796.35, 2803.53]
    _REGIONS: List[str] = ["FUV", "FUV", "NUV", "NUV"]
    _XW: List[int] = [380, 80, 37, 37]  # spectral pixels per window
    _YW: List[int] = [548, 548, 548, 548]  # spatial pixels per window
    _XS: List[int] = [0, 400, 0, 50]  # starting spectral pixel on CCD
    _YS: List[int] = [0, 0, 0, 0]  # starting spatial pixel on CCD

    _SJI_IDS: List[str] = ["SJI_1330", "SJI_1400", "SJI_2796", "SJI_2832"]
    _SJI_WAVELENGTHS: List[float] = [1330.0, 1400.0, 2796.0, 2832.0]

    _NRASTER: int = 30
    _NEXP_SJI: int = 5

    def __init__(self, filename: str = "muse_obs_20230101_000000_raster_t000_r00000.fits") -> None:
        self._filename = filename

    # ------------------------------------------------------------------
    # Basic observation shape
    # ------------------------------------------------------------------

    def getnwin(self) -> int:
        """Return number of spectral line windows."""
        return len(self._LINE_IDS)

    def getnraster(self, iwin: Optional[int] = None) -> Union[np.ndarray, int]:
        """Return number of raster positions (per window or as an array)."""
        arr = np.full(self.getnwin(), self._NRASTER, dtype=int)
        if iwin is not None:
            return int(arr[iwin])
        return arr

    # ------------------------------------------------------------------
    # Line window metadata
    # ------------------------------------------------------------------

    def getobsid(self) -> str:
        """Return the observation ID string."""
        return "3620509453"

    def getline_id(self, i: Optional[int] = None) -> Union[str, List[str]]:
        """Return the spectral line ID for window *i*, or all IDs if *i* is None."""
        if i is None:
            return list(self._LINE_IDS)
        return self._LINE_IDS[i]

    def getline_wvl(self, i: int, wscale: str = "pixels") -> float:
        """
        Return the central wavelength of window *i*.

        Parameters
        ----------
        i : int
            Window index.
        wscale : {"pixels", "AA"}
            Return value in detector pixels or Angstrom.
        """
        if wscale == "AA":
            return self._LINE_WVL_AA[i]
        return self._XW[i] / 2.0

    def getxw(self, i: Optional[int] = None) -> Union[int, List[int]]:
        """Return spectral width in pixels for window *i* or all windows."""
        if i is None:
            return list(self._XW)
        return self._XW[i]

    def getyw(self, i: Optional[int] = None) -> Union[int, List[int]]:
        """Return spatial height in pixels for window *i* or all windows."""
        if i is None:
            return list(self._YW)
        return self._YW[i]

    def getxs(self, i: Optional[int] = None) -> Union[int, List[int]]:
        """Return starting spectral pixel on the CCD for window *i* or all."""
        if i is None:
            return list(self._XS)
        return self._XS[i]

    def getys(self, i: Optional[int] = None) -> Union[int, List[int]]:
        """Return starting spatial pixel on the CCD for window *i* or all."""
        if i is None:
            return list(self._YS)
        return self._YS[i]

    def getregion(self, i: Optional[int] = None) -> Union[str, List[str]]:
        """Return detector region ("FUV" or "NUV") for window *i* or all."""
        if i is None:
            return list(self._REGIONS)
        return self._REGIONS[i]

    # ------------------------------------------------------------------
    # FITS header
    # ------------------------------------------------------------------

    def gethdr(self, iext: int = 0) -> List[str]:
        """
        Return FITS-style header card strings for extension *iext*.

        Extension 0 is the primary header; extensions 1..nwin are
        per-window headers.
        """
        primary = [
            "SIMPLE  =                    T / file does conform to FITS standard",
            "BITPIX  =                  -32 / number of bits per data pixel",
            "NAXIS   =                    3 / number of data axes",
            "EXTEND  =                    T / FITS dataset may contain extensions",
            "DATE_OBS= '2023-01-01T00:00:00' / date of observation",
            "TELESCOP= 'MUSE    '           / telescope name",
            "INSTRUME= 'MUSE    '           / instrument name",
            "OBSID   = '3620509453'         / observation ID",
            "OBS_DESC= 'Large dense 320-step raster' / observation description",
            "OBSLABEL= 'MUSE-obs'           / observation label",
            "OBSTITLE= 'Generic raster'     / observation title",
            "XCEN    =               0.00   / slit centre, arcsec from Sun centre (x)",
            "YCEN    =               0.00   / slit centre, arcsec from Sun centre (y)",
            "FOVX    =              60.00   / field of view in x, arcsec",
            "FOVY    =             120.00   / field of view in y, arcsec",
            "SAT_ROT =               0.00   / spacecraft roll angle, deg",
        ]
        nw = self.getnwin()
        if iext == 0:
            return primary
        if 1 <= iext <= nw:
            i = iext - 1
            extra = [
                f"EXTNAME = '{self._LINE_IDS[i]:<8}'        / window identifier",
                f"WAVEMIN =  {self._LINE_WVL_AA[i] - 1.0:.3f}  / minimum wavelength (AA)",
                f"WAVEMAX =  {self._LINE_WVL_AA[i] + 1.0:.3f}  / maximum wavelength (AA)",
                f"NAXIS1  =  {self._XW[i]:5d}            / spectral pixels",
                f"NAXIS2  =  {self._YW[i]:5d}            / spatial pixels",
                f"NAXIS3  =  {self._NRASTER:5d}            / raster positions",
                f"REGION  = '{self._REGIONS[i]:<3}'               / detector region",
            ]
            return primary + extra
        return primary

    # ------------------------------------------------------------------
    # Pointing / coordinates
    # ------------------------------------------------------------------

    def getfilename(self) -> str:
        """Return the logical filename."""
        return self._filename

    def getdate_obs(self) -> str:
        """Return the observation date-time string."""
        return "2023-01-01T00:00:00"

    def getxcen(self) -> np.ndarray:
        """Return slit x-centre in arcsec (array, one value per raster)."""
        return np.zeros(self._NRASTER)

    def getycen(self) -> np.ndarray:
        """Return slit y-centre in arcsec."""
        return np.zeros(self._NRASTER)

    def getfovx(self) -> np.ndarray:
        """Return field-of-view in x, arcsec."""
        return np.array([60.0])

    def getfovy(self) -> np.ndarray:
        """Return field-of-view in y, arcsec."""
        return np.array([120.0])

    # ------------------------------------------------------------------
    # Generic keyword lookup
    # ------------------------------------------------------------------

    def getinfo(self, key: str, *args, **kwargs):
        """
        Return a scalar header keyword value.

        Recognised keys: DATE_OBS, OBS_DESC, OBSLABEL, OBSTITLE, SAT_ROT.
        Unknown keys return an empty string.
        """
        _table = {
            "DATE_OBS": "2023-01-01T00:00:00",
            "OBS_DESC": "Large dense 320-step raster",
            "OBSLABEL": "MUSE-obs",
            "OBSTITLE": "Generic raster",
            "SAT_ROT": 0.0,
        }
        return _table.get(key, "")

    # ------------------------------------------------------------------
    # Slit-jaw imager (SJI)
    # ------------------------------------------------------------------

    def getread_sji(self) -> np.ndarray:
        """Return an array indicating which SJI channels have data (1 = yes)."""
        return np.ones(len(self._SJI_IDS), dtype=int)

    def getsji_id(self, index=None) -> List[str]:
        """Return SJI channel identifiers."""
        if index is None:
            return list(self._SJI_IDS)
        return [self._SJI_IDS[i] for i in np.atleast_1d(index)]

    def getsji(self, lwin: int, noload: bool = False) -> np.ndarray:
        """
        Return a SJI image cube shaped (nx, ny, nexp) for channel *lwin*.

        The data are reproducible random Poisson counts.
        """
        rng = np.random.default_rng(seed=lwin)
        peak = 1000 if self._SJI_IDS[lwin].endswith("2796") else 500
        return rng.poisson(peak, size=(150, 150, self._NEXP_SJI)).astype(np.float32)

    def getnexp_sji(self, lwin: int) -> int:
        """Return number of SJI exposures for channel *lwin*."""
        return self._NEXP_SJI

    def getfovx_sji(self, lwin: int) -> float:
        """Return SJI field-of-view in x, arcsec."""
        return 60.0

    def getfovy_sji(self, lwin: int) -> float:
        """Return SJI field-of-view in y, arcsec."""
        return 60.0

    # ------------------------------------------------------------------
    # Spectral data and descaling
    # ------------------------------------------------------------------

    def getvar(self, i: int, noscale: bool = False) -> np.ndarray:
        """
        Return a spectral data cube shaped (lambda, y, t) for window *i*.

        Values are reproducible random Poisson counts (int16).
        """
        rng = np.random.default_rng(seed=i)
        return rng.poisson(200, size=(self._XW[i], self._YW[i], self._NRASTER)).astype(np.int16)

    def descale_array(self, data: np.ndarray) -> np.ndarray:
        """Convert scaled integer data to physical float values."""
        return data.astype(np.float32)

    def missing(self) -> float:
        """Return the missing-data fill value."""
        return -200.0

    # ------------------------------------------------------------------
    # Binning / CCD geometry helpers
    # ------------------------------------------------------------------

    def binning_spectral(self) -> np.ndarray:
        """Return spectral binning factor for each window (1 = unbinned)."""
        return np.ones(self.getnwin(), dtype=int)

    def binning_region(self, region: str) -> int:
        """Return the spectral binning for all windows in detector *region*."""
        return 1

    def getccd_sz(self, region: str) -> np.ndarray:
        """Return CCD size [nx, ny] in pixels for the given detector region."""
        if region.upper() == "FUV":
            return np.array([4096, 1024])
        return np.array([2048, 1024])
