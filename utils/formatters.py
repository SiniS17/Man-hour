"""
Formatter Utilities Module
Handles string formatting, cleaning, and display formatting
"""

import pandas as pd


def clean_string(value):
    """
    Cleans a string value by removing extra whitespace and handling None/NaN.

    Args:
        value: Value to clean (can be str, None, NaN, etc.)

    Returns:
        str: Cleaned string, or empty string if None/NaN

    Examples:
        >>> clean_string("  hello  ")
        'hello'
        >>> clean_string(None)
        ''
    """
    if pd.isna(value) or value is None:
        return ""

    return str(value).strip()


def format_percentage(value, decimal_places=1):
    """
    Formats a decimal value as a percentage string.

    Args:
        value (float): Decimal value (e.g., 0.25 for 25%)
        decimal_places (int): Number of decimal places to show

    Returns:
        str: Formatted percentage string (e.g., "25.0%")

    Examples:
        >>> format_percentage(0.255, 1)
        '25.5%'
        >>> format_percentage(0.5, 2)
        '50.00%'
    """
    if pd.isna(value):
        return "0.0%"

    percentage = value * 100
    return f"{percentage:.{decimal_places}f}%"


def truncate_string(value, max_length=30, suffix="..."):
    """
    Truncates a string to a maximum length.

    Args:
        value: String value to truncate
        max_length (int): Maximum length including suffix
        suffix (str): Suffix to add if truncated

    Returns:
        str: Truncated string

    Examples:
        >>> truncate_string("This is a very long string", 10)
        'This is...'
    """
    value_str = clean_string(value)

    if len(value_str) <= max_length:
        return value_str

    return value_str[:max_length - len(suffix)] + suffix


def format_seq_display(seq_value):
    """
    Formats a SEQ value for display.

    Args:
        seq_value: SEQ value (can be float, string, etc.)

    Returns:
        str: Formatted SEQ string

    Examples:
        >>> format_seq_display(2.1)
        '2.1'
        >>> format_seq_display('3.45')
        '3.45'
    """
    if pd.isna(seq_value):
        return "N/A"

    return str(seq_value).strip()


def format_task_id_display(task_id):
    """
    Formats a task ID for display, handling None and 'nan' values.

    Args:
        task_id: Task ID value

    Returns:
        str: Formatted task ID or "(No ID)"

    Examples:
        >>> format_task_id_display("24-045-00")
        '24-045-00'
        >>> format_task_id_display(None)
        '(No ID)'
    """
    if pd.isna(task_id) or str(task_id).lower() == 'nan':
        return "(No ID)"

    return str(task_id).strip()


def format_special_code_display(special_code):
    """
    Formats a special code for display.

    Args:
        special_code: Special code value

    Returns:
        str: Formatted special code or "(No Code)"

    Examples:
        >>> format_special_code_display("ABC")
        'ABC'
        >>> format_special_code_display(None)
        '(No Code)'
    """
    if pd.isna(special_code):
        return "(No Code)"

    code_str = str(special_code).strip()

    if code_str == '' or code_str.lower() == 'nan':
        return "(No Code)"

    return code_str


def format_tool_type(tool_type_value):
    """
    Formats tool type value ('Y'/'N') to readable string.

    Args:
        tool_type_value: Tool type indicator ('Y', 'N', or other)

    Returns:
        str: 'Tool', 'Spare', or 'Unknown'

    Examples:
        >>> format_tool_type('Y')
        'Tool'
        >>> format_tool_type('N')
        'Spare'
    """
    if pd.isna(tool_type_value):
        return 'Unknown'

    val_str = str(tool_type_value).strip().upper()

    if val_str == 'Y':
        return 'Tool'
    elif val_str == 'N':
        return 'Spare'
    else:
        return str(tool_type_value)


def format_column_width(df, column_name, min_width=15, max_width=50):
    """
    Calculates appropriate column width for Excel export.

    Args:
        df (pd.DataFrame): DataFrame containing the column
        column_name (str): Name of column
        min_width (int): Minimum column width
        max_width (int): Maximum column width

    Returns:
        int: Recommended column width
    """
    if column_name not in df.columns:
        return min_width

    # Get max length of values in column
    max_length = df[column_name].astype(str).apply(len).max()

    # Also consider column name length
    header_length = len(str(column_name))

    # Take the maximum
    length = max(max_length, header_length)

    # Apply min/max constraints
    width = min(max(length + 2, min_width), max_width)

    return width