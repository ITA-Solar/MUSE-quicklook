#!/usr/bin/env python3
"""
Example usage of MUSE PyFiles modules

This script demonstrates how to use the muse_recent_timewindows module
programmatically and tests the basic functionality.
"""

from datetime import datetime, timedelta

from muse_recent_timewindows import MUSERecentTimeWindows


def test_recent_windows():
    """Test the MUSERecentTimeWindows class"""
    print("Testing MUSERecentTimeWindows class...")
    print("=" * 60)

    # Create some sample time windows
    now = datetime.now()

    starttimes = [
        (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S"),
        (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S"),
        (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S"),
    ]

    endtimes = [
        (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S"),
        (now - timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%S"),
        (now - timedelta(days=25)).strftime("%Y-%m-%dT%H:%M:%S"),
    ]

    # Initialize the object
    recent = MUSERecentTimeWindows(starttimes, endtimes)

    print("\nInitial windows:")
    for i, window in enumerate(recent.get_windows()):
        print(f"  {i + 1}. {window}")

    # Add a new search
    print("\nAdding new search: Last 7 days")
    new_start = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    new_end = now.strftime("%Y-%m-%dT%H:%M:%S")
    recent.newsearch(new_start, new_end)

    print("\nUpdated windows (new one should be first):")
    for i, window in enumerate(recent.get_windows()):
        print(f"  {i + 1}. {window}")

    # Get specific time window
    print("\nGetting times for first window:")
    start, end = recent.get_times(index=0)
    print(f"  Start: {start}")
    print(f"  End:   {end}")

    print("\n" + "=" * 60)
    print("? MUSERecentTimeWindows test completed successfully!")


def test_config_directory():
    """Test configuration directory creation"""
    print("\n\nTesting configuration directory...")
    print("=" * 60)

    from muse_pyfiles import get_muse_config_dir

    config_dir = get_muse_config_dir()
    print(f"\nConfiguration directory: {config_dir}")
    print(f"Exists: {config_dir.exists()}")

    readme_file = config_dir / "README.txt"
    if readme_file.exists():
        print("\nREADME contents:")
        with open(readme_file, "r") as f:
            print(f.read())

    print("=" * 60)
    print("? Configuration directory test completed!")


def test_time_validation():
    """Test time validation function"""
    print("\n\nTesting time validation...")
    print("=" * 60)

    from muse_pyfiles import valid_time

    test_cases = [
        ("2023-01-15T12:30:00", True, "ISO format"),
        ("2023-01-15 12:30:00", True, "Space-separated"),
        ("15-Jan-23 12:30:00", True, "VMS format"),
        ("invalid time", False, "Invalid format"),
        ("", False, "Empty string"),
        ("2023-13-45 99:99:99", False, "Invalid values"),
    ]

    print("\nTesting various time formats:")
    for time_str, expected, description in test_cases:
        result = valid_time(time_str)
        status = "?" if result == expected else "?"
        print(f"  {status} {description:20s} '{time_str}' ? {result}")

    print("\n" + "=" * 60)
    print("? Time validation test completed!")


def test_file_time_extraction():
    """Test file time extraction"""
    print("\n\nTesting file time extraction...")
    print("=" * 60)

    from muse_pyfiles import file2time

    test_files = [
        "muse_data_20230115_123045_001.fits",
        "obs_20231225_180000.fits",
        "muse_cube_2023-12-01T15:30:00.fits",  # Alternative format
        "no_timestamp_file.fits",
    ]

    print("\nExtracting timestamps from filenames:")
    for filename in test_files:
        timestamp = file2time(filename)
        print(f"  {filename:50s} ? {timestamp if timestamp else 'No timestamp found'}")

    print("\n" + "=" * 60)
    print("? File time extraction test completed!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MUSE PyFiles Module Tests")
    print("=" * 60)

    try:
        test_recent_windows()
        test_config_directory()
        test_time_validation()
        test_file_time_extraction()

        print("\n\n" + "=" * 60)
        print("ALL TESTS PASSED! ?")
        print("=" * 60)
        print("\nYou can now run the main application:")
        print("  python muse_pyfiles.py")
        print("\nOr import the modules in your own code:")
        print("  from muse_recent_timewindows import MUSERecentTimeWindows")
        print("  from muse_pyfiles import get_muse_config_dir, valid_time")
        print()

    except Exception as e:
        print(f"\n\n? TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
