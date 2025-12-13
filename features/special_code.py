"""
Special Code Module
Handles special code distribution calculations and analysis
"""

from core.config import SPECIAL_CODE_COLUMN


def calculate_special_code_distribution(df):
    """
    Calculate the distribution of planned hours by special code.

    Args:
        df (pd.DataFrame): DataFrame with special code and adjusted hours

    Returns:
        dict: Sorted dictionary of {special_code: total_hours}
    """
    # Group by special code and sum the adjusted hours
    special_code_groups = df.groupby(SPECIAL_CODE_COLUMN)['Adjusted Hours'].sum()

    # Sort by hours (descending) and convert to dictionary
    special_code_dict = special_code_groups.sort_values(ascending=False).to_dict()

    return special_code_dict


def calculate_special_code_per_day(special_code_distribution, workpack_days):
    """
    Calculate average hours per day for each special code.

    Args:
        special_code_distribution (dict): Dictionary of {special_code: total_hours}
        workpack_days (int): Number of days in the workpack

    Returns:
        dict: Dictionary of {special_code: hours_per_day} or None if workpack_days is invalid
    """
    if not workpack_days or workpack_days <= 0:
        return None

    return {
        code: hours / workpack_days
        for code, hours in special_code_distribution.items()
    }


def get_special_code_summary(special_code_distribution, total_hours):
    """
    Generate a summary of special code distribution with percentages.

    Args:
        special_code_distribution (dict): Dictionary of {special_code: total_hours}
        total_hours (float): Total man-hours across all special codes

    Returns:
        list: List of dictionaries with code, hours, and percentage
    """
    if total_hours <= 0:
        return []

    summary = []
    for code, hours in special_code_distribution.items():
        percentage = (hours / total_hours) * 100
        summary.append({
            'code': code,
            'hours': hours,
            'percentage': percentage
        })

    return summary


def validate_special_code_column(df, special_code_column):
    """
    Validate that the special code column exists and has data.

    Args:
        df (pd.DataFrame): Input DataFrame
        special_code_column (str): Name of special code column

    Returns:
        tuple: (is_valid, error_message)
    """
    if special_code_column is None:
        return False, "Special code column is not configured in settings.ini"

    if special_code_column not in df.columns:
        return False, f"Column '{special_code_column}' not found in file"

    # Check if column has any non-null values
    non_null_count = df[special_code_column].notna().sum()
    if non_null_count == 0:
        return False, f"Column '{special_code_column}' has no data"

    return True, ""