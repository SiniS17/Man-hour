"""
Validation Utilities Module
Handles data validation, column checking, and data quality checks
"""

import pandas as pd


def validate_required_columns(df, required_columns, file_name="file"):
    """
    Validates that all required columns exist in the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to validate
        required_columns (list): List of required column names
        file_name (str): Name of file being validated (for error messages)

    Returns:
        tuple: (bool: is_valid, list: missing_columns)

    Raises:
        ValueError: If any required columns are missing
    """
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(
            f"Missing required columns in {file_name}. "
            f"Expected: {required_columns}, Missing: {missing_columns}"
        )

    return True, []


def check_column_exists(df, column_name, file_name="file"):
    """
    Checks if a single column exists in the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to check
        column_name (str): Column name to look for
        file_name (str): Name of file being checked (for messages)

    Returns:
        bool: True if column exists, False otherwise
    """
    if column_name not in df.columns:
        print(f"WARNING: Column '{column_name}' not found in {file_name}.")
        print(f"Available columns: {list(df.columns)}")
        return False
    return True


def validate_numeric_column(df, column_name, allow_na=True):
    """
    Validates that a column contains numeric data.

    Args:
        df (pd.DataFrame): DataFrame containing the column
        column_name (str): Name of column to validate
        allow_na (bool): Whether to allow NaN values

    Returns:
        tuple: (bool: is_valid, list: problematic_indices)
    """
    if column_name not in df.columns:
        return False, []

    column = df[column_name]

    # Try converting to numeric
    numeric_column = pd.to_numeric(column, errors='coerce')

    # Find non-numeric values (excluding NaN if allowed)
    if allow_na:
        problematic = column[numeric_column.isna() & column.notna()]
    else:
        problematic = column[numeric_column.isna()]

    if len(problematic) > 0:
        return False, problematic.index.tolist()

    return True, []


def check_empty_values(df, column_name, threshold=0.5):
    """
    Checks if a column has too many empty/null values.

    Args:
        df (pd.DataFrame): DataFrame containing the column
        column_name (str): Name of column to check
        threshold (float): Maximum allowed proportion of empty values (0.0-1.0)

    Returns:
        tuple: (bool: passes_check, float: empty_proportion)
    """
    if column_name not in df.columns:
        return False, 1.0

    total_rows = len(df)
    if total_rows == 0:
        return True, 0.0

    # Count empty values (NaN, None, empty strings)
    empty_count = df[column_name].isna().sum()
    empty_count += (df[column_name].astype(str).str.strip() == '').sum()

    empty_proportion = empty_count / total_rows

    passes = empty_proportion <= threshold

    return passes, empty_proportion


def validate_date_columns(df, start_col='Start_date', end_col='End_date'):
    """
    Validates date columns and checks if end date is after start date.

    Args:
        df (pd.DataFrame): DataFrame containing date columns
        start_col (str): Name of start date column
        end_col (str): Name of end date column

    Returns:
        tuple: (bool: is_valid, str: error_message)
    """
    if start_col not in df.columns or end_col not in df.columns:
        return False, f"Date columns '{start_col}' or '{end_col}' not found"

    try:
        start_date = pd.to_datetime(df[start_col].iloc[0])
        end_date = pd.to_datetime(df[end_col].iloc[0])

        if end_date < start_date:
            return False, f"End date ({end_date}) is before start date ({start_date})"

        return True, ""

    except Exception as e:
        return False, f"Error parsing dates: {e}"


def validate_seq_format(seq_value):
    """
    Validates that a SEQ value follows the expected format (e.g., "2.1", "3.45").

    Args:
        seq_value: SEQ value to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if pd.isna(seq_value):
        return False

    seq_str = str(seq_value).strip()

    # Should contain at least one dot
    if '.' not in seq_str:
        return False

    # Split and check parts are numeric
    parts = seq_str.split('.')
    if len(parts) < 2:
        return False

    try:
        # Major version should be numeric
        int(parts[0])
        # Minor version should be numeric
        int(parts[1])
        return True
    except ValueError:
        return False