"""
Time Utilities Module
Handles all time-related conversions and formatting
"""

import pandas as pd
from datetime import timedelta


def hours_to_hhmm(hours):
    """
    Converts a float representing total hours (e.g., 36.5) into an HH:MM string (e.g., "36:30").

    Args:
        hours (float): Total hours (can be decimal)

    Returns:
        str: Formatted string in HH:MM format

    Examples:
        >>> hours_to_hhmm(36.5)
        '36:30'
        >>> hours_to_hhmm(2.25)
        '02:15'
    """
    if hours < 0:
        return "00:00"

    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60

    return f"{h:02d}:{m:02d}"


def convert_planned_mhrs(time_val):
    """
    Converts planned man-hours from minutes to hours.
    The input is in minutes (numeric value).

    Args:
        time_val: Numeric value in minutes, or a string representation

    Returns:
        float: Hours (converted from minutes)

    Examples:
        >>> convert_planned_mhrs(120)
        2.0
        >>> convert_planned_mhrs(90)
        1.5
    """
    if pd.isna(time_val):
        return 0.0

    if isinstance(time_val, (int, float)):
        # Input is in minutes, convert to hours
        return float(time_val) / 60.0

    try:
        # Try to parse as numeric string
        minutes = float(str(time_val).strip())
        return minutes / 60.0
    except Exception as e:
        print(f"Error converting minutes to hours: {e}")

    return 0.0


def time_to_hours(time_val):
    """
    Converts Excel time values (which may include days, e.g., '1 day 12:30:00')
    into a float representing total hours.

    This function handles various time formats from Excel including:
    - timedelta objects
    - Decimal values (Excel's time format)
    - String representations of time

    Args:
        time_val: Time value in various formats

    Returns:
        float: Total hours

    Examples:
        >>> time_to_hours(timedelta(hours=2, minutes=30))
        2.5
        >>> time_to_hours(0.5)  # Excel format for 12 hours
        12.0
    """
    if pd.isna(time_val):
        return 0.0

    # Handle timedelta objects
    if isinstance(time_val, timedelta):
        return time_val.total_seconds() / 3600.0

    # Handle numeric values (Excel's decimal time format)
    if isinstance(time_val, (float, int)):
        # Excel stores time as fraction of a day
        # 0.5 = 12 hours, 1.0 = 24 hours
        if 0 < time_val < 1:
            return time_val * 24.0
        else:
            return float(time_val)

    # Handle string representations
    try:
        time_str = str(time_val).strip()
        if time_str.count(':') >= 1:
            return pd.to_timedelta(time_str).total_seconds() / 3600.0
    except Exception:
        pass

    return 0.0


def calculate_workpack_duration(start_date, end_date):
    """
    Calculate the duration of a workpack in days.

    Args:
        start_date: Start date (datetime or pandas Timestamp)
        end_date: End date (datetime or pandas Timestamp)

    Returns:
        int: Number of days (inclusive of both start and end)
    """
    if pd.isna(start_date) or pd.isna(end_date):
        return None

    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return (end - start).days + 1  # +1 to include both start and end day
    except Exception:
        return None