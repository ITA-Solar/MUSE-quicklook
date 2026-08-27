"""
MUSE Recent Time Windows

This module contains a class that manages recent time windows used in file searches.
When there is a new search, this object reorders the time windows, and adds and/or
deletes time windows if necessary.

Author: Translated from IDL to Python
Original IDL version by Martin Wiesmann (2013)
"""

from astropy.time import Time


class MUSERecentTimeWindows:
    """
    Class to manage recent time windows used in searches.

    Maintains up to maxnum (default 10) recent time window searches,
    automatically reordering and managing the list as new searches are added.
    """

    def __init__(
        self,
        starttimes: list[str] | None = None,
        endtimes: list[str] | None = None,
        maxnum: int = 10,
    ):
        """
        Initialize the recent time windows object.

        Parameters
        ----------
        starttimes : list of str, optional
            List of start times in a parseable format
        endtimes : list of str, optional
            List of end times in a parseable format
        maxnum : int, optional
            Maximum number of time windows to track (default: 10)
        """
        self.maxnum = maxnum
        self.num = 0

        # Initialize storage arrays
        self.starttimes = [""] * maxnum
        self.endtimes = [""] * maxnum
        self.starts = [None] * maxnum  # Will hold Time objects
        self.ends = [None] * maxnum  # Will hold Time objects
        self.window = [""] * maxnum

        # Populate if initial times provided
        if starttimes is not None and endtimes is not None:
            n = min(len(starttimes), len(endtimes), maxnum)
            self.num = n

            if n > 0:
                for i in range(n):
                    self.starttimes[i] = starttimes[i]
                    self.endtimes[i] = endtimes[i]
                    try:
                        self.starts[i] = Time(starttimes[i], scale="utc")
                        self.ends[i] = Time(endtimes[i], scale="utc")
                        # Create window display string
                        start_date = self.starts[i].datetime.strftime("%d-%b-%Y")
                        end_date = self.ends[i].datetime.strftime("%d-%b-%Y")
                        self.window[i] = f"{start_date} - {end_date}"
                    except Exception as e:
                        print(f"Warning: Could not parse time at index {i}: {e}")

    def get_times(self, index: int | None = None) -> tuple[list[str], list[str]]:
        """
        Get the start and end times.

        Parameters
        ----------
        index : int, optional
            If provided, return only the times at this index.
            Otherwise return all active time windows.

        Returns
        -------
        starttimes : list of str
            List of start time strings
        endtimes : list of str
            List of end time strings
        """
        if index is not None:
            return self.starttimes[index], self.endtimes[index]
        else:
            return self.starttimes[: self.num], self.endtimes[: self.num]

    def get_windows(self) -> list[str]:
        """
        Get the formatted window strings for display.

        Returns
        -------
        list of str
            Formatted time window strings (e.g., "01-Jan-2023 - 05-Jan-2023")
        """
        return self.window[: self.num]

    def newsearch(self, starttime: str, endtime: str):
        """
        Add a new search to the time window list.

        This method reorders the list, placing the new (or existing matching)
        time window at the top. If the list is full and this is a new window,
        the oldest entry is removed.

        Parameters
        ----------
        starttime : str
            Start time string in a parseable format
        endtime : str
            End time string in a parseable format
        """
        try:
            startt = Time(starttime, scale="utc")
            endt = Time(endtime, scale="utc")
        except Exception as e:
            print(f"Error parsing times in newsearch: {e}")
            return

        # Create window string
        start_date = startt.datetime.strftime("%d-%b-%Y")
        end_date = endt.datetime.strftime("%d-%b-%Y")
        windt = f"{start_date} - {end_date}"

        # Check if this window already exists
        try:
            ind = self.window.index(windt)
            exists = True
        except ValueError:
            ind = -1
            exists = False

        if exists and ind > 0:
            # Window exists but not at position 0 - need to reorder
            # Move everything between 0 and ind-1 down by one
            temp_starttimes = self.starttimes.copy()
            temp_endtimes = self.endtimes.copy()
            temp_starts = self.starts.copy()
            temp_ends = self.ends.copy()
            temp_window = self.window.copy()

            # Shift items 0 to ind-1 down by one position
            for i in range(ind, 0, -1):
                self.starttimes[i] = temp_starttimes[i - 1]
                self.endtimes[i] = temp_endtimes[i - 1]
                self.starts[i] = temp_starts[i - 1]
                self.ends[i] = temp_ends[i - 1]
                self.window[i] = temp_window[i - 1]

            # Place the found window at position 0
            self.starttimes[0] = temp_starttimes[ind]
            self.endtimes[0] = temp_endtimes[ind]
            self.starts[0] = temp_starts[ind]
            self.ends[0] = temp_ends[ind]
            self.window[0] = temp_window[ind]

        elif not exists:
            # New window - shift everything down by one
            for i in range(self.maxnum - 1, 0, -1):
                self.starttimes[i] = self.starttimes[i - 1]
                self.endtimes[i] = self.endtimes[i - 1]
                self.starts[i] = self.starts[i - 1]
                self.ends[i] = self.ends[i - 1]
                self.window[i] = self.window[i - 1]

            # Increment count if we haven't reached max
            if self.num < self.maxnum:
                self.num += 1

            # Add new window at position 0
            self.starttimes[0] = starttime
            self.endtimes[0] = endtime
            self.starts[0] = startt
            self.ends[0] = endt
            self.window[0] = windt
        # If exists and ind == 0, window is already at top - do nothing
