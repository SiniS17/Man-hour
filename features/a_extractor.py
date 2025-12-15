"""
A Column Extractor Module
Extracts ac_type and wp_type from column A for bonus hours lookup
"""

import pandas as pd
import os
from core.config import A_COLUMN, REFERENCE_FOLDER, BONUS_HOURS_FILE, BONUS_HOURS_SHEET


def extract_ac_type_and_check(value):
    """
    Extract ac_type and wp_type from a column value.

    Rules:
    - ac_type: Everything before the first '-'
    - wp_type: Everything after the last '-'

    Args:
        value: String value from column A (e.g., "a21-b-c-dee")

    Returns:
        tuple: (ac_type, wp_type)

    Examples:
        >>> extract_ac_type_and_check("a21-b-c-dee")
        ('a21', 'dee')
        >>> extract_ac_type_and_check("simple-value")
        ('simple', 'value')
        >>> extract_ac_type_and_check("no-dash")
        ('no', 'dash')
    """
    if pd.isna(value):
        return None, None

    value_str = str(value).strip()

    if '-' not in value_str:
        # No dash found, return the whole string for both
        return value_str, value_str

    # Split by dash
    parts = value_str.split('-')

    # ac_type: first part (before first dash)
    ac_type = parts[0].strip()

    # wp_type: last part (after last dash)
    wp_type = parts[-1].strip()

    return ac_type, wp_type


def extract_from_dataframe(df):
    """
    Extract ac_type and wp_type from the first row of column A in dataframe.
    Since all rows in column A are the same, we only need the first row.

    Args:
        df: Input DataFrame

    Returns:
        tuple: (ac_type, wp_type)
    """
    if A_COLUMN not in df.columns:
        print(f"WARNING: Column '{A_COLUMN}' not found in file")
        print(f"Available columns: {list(df.columns)}")
        return None, None

    if len(df) == 0:
        print(f"WARNING: DataFrame is empty, cannot extract from column '{A_COLUMN}'")
        return None, None

    # Get the first value from column A
    first_value = df[A_COLUMN].iloc[0]

    # Extract ac_type and wp_type
    ac_type, wp_type = extract_ac_type_and_check(first_value)

    print(f"Extracted from '{A_COLUMN}': ac_type='{ac_type}', wp_type='{wp_type}'")

    return ac_type, wp_type


def load_bonus_hours_lookup():
    """
    Load bonus hours lookup table from REFERENCE folder.

    Expected format:
    - Columns: ac_type, wp_type, bonus_hours
    - Each row contains a combination of ac_type and wp_type with corresponding bonus hours

    Returns:
        dict: Nested dictionary {ac_type: {wp_type: bonus_hours}}
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
        required_cols = ['ac_type', 'wp_type', 'bonus_hours']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"WARNING: Bonus hours file missing columns: {missing_cols}")
            print(f"Available columns: {list(df.columns)}")
            return {}

        # Build nested dictionary
        bonus_lookup = {}

        for idx, row in df.iterrows():
            ac_type = str(row['ac_type']).strip()
            wp_type = str(row['wp_type']).strip()
            bonus_hours = float(row['bonus_hours'])

            if ac_type not in bonus_lookup:
                bonus_lookup[ac_type] = {}

            bonus_lookup[ac_type][wp_type] = bonus_hours

        print(f"Loaded bonus hours lookup: {len(df)} entries")

        return bonus_lookup

    except Exception as e:
        print(f"ERROR loading bonus hours file: {e}")
        return {}


def get_bonus_hours(ac_type, wp_type, bonus_lookup):
    """
    Look up bonus hours for given ac_type and wp_type.

    Args:
        ac_type: Type extracted from column A
        wp_type: Check value extracted from column A
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        float: Bonus hours (0.0 if not found)
    """
    if not bonus_lookup:
        return 0.0

    if ac_type not in bonus_lookup:
        return 0.0

    if wp_type not in bonus_lookup[ac_type]:
        return 0.0

    return bonus_lookup[ac_type][wp_type]


def apply_bonus_hours(df, ac_type, wp_type, bonus_lookup):
    """
    Apply bonus hours to the DataFrame based on ac_type and wp_type.
    Adds bonus hours to 'Adjusted Hours' column.

    Args:
        df: DataFrame with 'Adjusted Hours' column
        ac_type: Type extracted from column A
        wp_type: Check value extracted from column A
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        DataFrame: Updated DataFrame with bonus hours applied
    """
    if 'Adjusted Hours' not in df.columns:
        print("WARNING: 'Adjusted Hours' column not found, cannot apply bonus hours")
        return df

    # Get bonus hours for this combination
    bonus_hours = get_bonus_hours(ac_type, wp_type, bonus_lookup)

    if bonus_hours > 0:
        print(f"Applying bonus hours: +{bonus_hours:.2f} hours for ac_type='{ac_type}', wp_type='{wp_type}'")
        df['Adjusted Hours'] = df['Adjusted Hours'] + bonus_hours
    else:
        print(f"No bonus hours found for ac_type='{ac_type}', wp_type='{wp_type}'")

    return df
