"""
A Column Extractor Module
Extracts a_type and a_check from column A for bonus hours lookup
"""

import pandas as pd
import os
from core.config import A_COLUMN, REFERENCE_FOLDER, BONUS_HOURS_FILE, BONUS_HOURS_SHEET


def extract_a_type_and_check(value):
    """
    Extract a_type and a_check from a column value.

    Rules:
    - a_type: Everything before the first '-'
    - a_check: Everything after the last '-'

    Args:
        value: String value from column A (e.g., "a21-b-c-dee")

    Returns:
        tuple: (a_type, a_check)

    Examples:
        >>> extract_a_type_and_check("a21-b-c-dee")
        ('a21', 'dee')
        >>> extract_a_type_and_check("simple-value")
        ('simple', 'value')
        >>> extract_a_type_and_check("no-dash")
        ('no', 'dash')
    """
    if pd.isna(value):
        return (None, None)

    value_str = str(value).strip()

    if '-' not in value_str:
        # No dash found, return the whole string for both
        return (value_str, value_str)

    # Split by dash
    parts = value_str.split('-')

    # a_type: first part (before first dash)
    a_type = parts[0].strip()

    # a_check: last part (after last dash)
    a_check = parts[-1].strip()

    return (a_type, a_check)


def extract_from_dataframe(df):
    """
    Extract a_type and a_check from the first row of column A in dataframe.
    Since all rows in column A are the same, we only need the first row.

    Args:
        df: Input DataFrame

    Returns:
        tuple: (a_type, a_check)
    """
    if A_COLUMN not in df.columns:
        print(f"WARNING: Column '{A_COLUMN}' not found in file")
        print(f"Available columns: {list(df.columns)}")
        return (None, None)

    if len(df) == 0:
        print(f"WARNING: DataFrame is empty, cannot extract from column '{A_COLUMN}'")
        return (None, None)

    # Get the first value from column A
    first_value = df[A_COLUMN].iloc[0]

    # Extract a_type and a_check
    a_type, a_check = extract_a_type_and_check(first_value)

    print(f"Extracted from '{A_COLUMN}': a_type='{a_type}', a_check='{a_check}'")

    return (a_type, a_check)


def load_bonus_hours_lookup():
    """
    Load bonus hours lookup table from REFERENCE folder.

    Expected format:
    - Columns: a_type, a_check, bonus_hours
    - Each row contains a combination of a_type and a_check with corresponding bonus hours

    Returns:
        dict: Nested dictionary {a_type: {a_check: bonus_hours}}
    """
    bonus_file_path = os.path.join(REFERENCE_FOLDER, BONUS_HOURS_FILE)

    if not os.path.exists(bonus_file_path):
        print(f"Info: Bonus hours file not found at {bonus_file_path}")
        print(f"      No bonus hours will be applied")
        return {}

    try:
        # Load the bonus hours file
        df = pd.read_excel(bonus_file_path, sheet_name=BONUS_HOURS_SHEET, engine='openpyxl')

        # Check for required columns
        required_cols = ['a_type', 'a_check', 'bonus_hours']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"WARNING: Bonus hours file missing columns: {missing_cols}")
            print(f"Available columns: {list(df.columns)}")
            return {}

        # Build nested dictionary
        bonus_lookup = {}

        for idx, row in df.iterrows():
            a_type = str(row['a_type']).strip()
            a_check = str(row['a_check']).strip()
            bonus_hours = float(row['bonus_hours'])

            if a_type not in bonus_lookup:
                bonus_lookup[a_type] = {}

            bonus_lookup[a_type][a_check] = bonus_hours

        print(f"Loaded bonus hours lookup: {len(df)} entries")

        return bonus_lookup

    except Exception as e:
        print(f"ERROR loading bonus hours file: {e}")
        return {}


def get_bonus_hours(a_type, a_check, bonus_lookup):
    """
    Look up bonus hours for given a_type and a_check.

    Args:
        a_type: Type extracted from column A
        a_check: Check value extracted from column A
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        float: Bonus hours (0.0 if not found)
    """
    if not bonus_lookup:
        return 0.0

    if a_type not in bonus_lookup:
        return 0.0

    if a_check not in bonus_lookup[a_type]:
        return 0.0

    return bonus_lookup[a_type][a_check]


def apply_bonus_hours(df, a_type, a_check, bonus_lookup):
    """
    Apply bonus hours to the DataFrame based on a_type and a_check.
    Adds bonus hours to 'Adjusted Hours' column.

    Args:
        df: DataFrame with 'Adjusted Hours' column
        a_type: Type extracted from column A
        a_check: Check value extracted from column A
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        DataFrame: Updated DataFrame with bonus hours applied
    """
    if 'Adjusted Hours' not in df.columns:
        print("WARNING: 'Adjusted Hours' column not found, cannot apply bonus hours")
        return df

    # Get bonus hours for this combination
    bonus_hours = get_bonus_hours(a_type, a_check, bonus_lookup)

    if bonus_hours > 0:
        print(f"Applying bonus hours: +{bonus_hours:.2f} hours for a_type='{a_type}', a_check='{a_check}'")
        df['Adjusted Hours'] = df['Adjusted Hours'] + bonus_hours
    else:
        print(f"No bonus hours found for a_type='{a_type}', a_check='{a_check}'")

    return df