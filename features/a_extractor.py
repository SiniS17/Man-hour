"""
Modified a_extractor.py
Extracts bonus hours from multiple sheets with columns A and B
"""

import pandas as pd
import os
from core.config import A_COLUMN, REFERENCE_FOLDER, BONUS_HOURS_FILE, AC_TYPE_FILE, BONUS_1, BONUS_2


def extract_ac_name_and_wp_type(value):
    """Extract ac_name and wp_type from a column value."""
    if pd.isna(value):
        return None, None

    value_str = str(value).strip()

    if '-' not in value_str:
        return value_str, value_str

    parts = value_str.split('-')
    ac_name = parts[0].strip()
    wp_type = parts[-1].strip()

    return ac_name, wp_type


def load_ac_type_lookup():
    """Load aircraft type lookup table from REFERENCE folder."""
    ac_type_file = os.path.join(REFERENCE_FOLDER, AC_TYPE_FILE)

    if not os.path.exists(ac_type_file):
        print(f"WARNING: Aircraft type lookup file not found at {ac_type_file}")
        return {}

    try:
        df = pd.read_excel(ac_type_file, engine='openpyxl')

        required_cols = ['Type', 'Regis']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"WARNING: Aircraft type file missing columns: {missing_cols}")
            return {}

        ac_lookup = {}
        for idx, row in df.iterrows():
            regis = str(row['Regis']).strip()
            ac_type = str(row['Type']).strip()
            ac_lookup[regis] = ac_type

        print(f"Loaded aircraft type lookup: {len(ac_lookup)} entries")
        return ac_lookup

    except Exception as e:
        print(f"ERROR loading aircraft type file: {e}")
        return {}


def get_ac_type_from_name(ac_name, ac_lookup):
    """Look up aircraft type from aircraft name."""
    if not ac_lookup or not ac_name:
        return None
    return ac_lookup.get(ac_name)


def extract_from_dataframe(df):
    """Extract ac_type, wp_type, and ac_name from dataframe."""
    if A_COLUMN not in df.columns:
        print(f"WARNING: Column '{A_COLUMN}' not found in file")
        return None, None, None

    if len(df) == 0:
        print(f"WARNING: DataFrame is empty")
        return None, None, None

    first_value = df[A_COLUMN].iloc[0]
    ac_name, wp_type = extract_ac_name_and_wp_type(first_value)

    print(f"Extracted from '{A_COLUMN}': ac_name='{ac_name}', wp_type='{wp_type}'")

    ac_lookup = load_ac_type_lookup()
    ac_type = get_ac_type_from_name(ac_name, ac_lookup)

    if ac_type:
        print(f"Looked up ac_type: '{ac_type}' for ac_name '{ac_name}'")
    else:
        print(f"WARNING: Could not find ac_type for ac_name '{ac_name}'")

    return ac_type, wp_type, ac_name


def load_bonus_hours_lookup():
    """
    Load bonus hours from ALL sheets in the bonus hours file.

    NEW BEHAVIOR:
    - Reads all sheets in the file
    - For each sheet, looks for columns defined in settings.ini (BONUS_1 and BONUS_2)
    - Uses ac_type and wp_type to find matching rows
    - Sums values from both bonus columns (null = 0)
    - Returns breakdown by sheet for reporting

    Returns:
        tuple: (total_bonus_dict, breakdown_list)
            - total_bonus_dict: {ac_type: {wp_type: total_bonus_from_all_sheets}}
            - breakdown_list: [{'bonus_from': sheet_name, 'bonus_mhr': hours}, ...]
    """
    bonus_file_path = os.path.join(REFERENCE_FOLDER, BONUS_HOURS_FILE)

    if not os.path.exists(bonus_file_path):
        print(f"Info: Bonus hours file not found at {bonus_file_path}")
        print(f"      No bonus hours will be applied")
        return {}, []

    try:
        # Get all sheet names
        xls = pd.ExcelFile(bonus_file_path, engine='openpyxl')
        sheet_names = xls.sheet_names

        print(f"\nBonus Hours: Found {len(sheet_names)} sheets in '{BONUS_HOURS_FILE}'")

        # Accumulate bonus hours across all sheets
        total_bonus_dict = {}
        breakdown_list = []

        for sheet_name in sheet_names:
            print(f"  Reading sheet: '{sheet_name}'")

            # Load the sheet
            df = pd.read_excel(bonus_file_path, sheet_name=sheet_name, engine='openpyxl')

            # Check for required columns
            required_cols = ['ac_type', 'wp_type', BONUS_1, BONUS_2]
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(f"    WARNING: Missing columns {missing_cols}, skipping sheet")
                continue

            # Process each row in the sheet
            sheet_total_bonus = 0

            for idx, row in df.iterrows():
                ac_type = str(row['ac_type']).strip() if pd.notna(row['ac_type']) else None
                wp_type = str(row['wp_type']).strip() if pd.notna(row['wp_type']) else None

                if not ac_type or not wp_type:
                    continue

                # Get values from bonus columns (null = 0)
                value_a = float(row[BONUS_1]) if pd.notna(row[BONUS_1]) else 0.0
                value_b = float(row[BONUS_2]) if pd.notna(row[BONUS_2]) else 0.0

                # Sum A and B
                total_bonus_for_row = value_a + value_b

                if total_bonus_for_row == 0:
                    continue

                # Add to sheet total
                sheet_total_bonus += total_bonus_for_row

                # Accumulate in total_bonus_dict
                if ac_type not in total_bonus_dict:
                    total_bonus_dict[ac_type] = {}

                if wp_type not in total_bonus_dict[ac_type]:
                    total_bonus_dict[ac_type][wp_type] = 0.0

                total_bonus_dict[ac_type][wp_type] += total_bonus_for_row

            # Add to breakdown list if this sheet contributed any bonus
            if sheet_total_bonus > 0:
                breakdown_list.append({
                    'bonus_from': sheet_name,
                    'bonus_mhr': sheet_total_bonus
                })
                print(f"    Sheet total: {sheet_total_bonus:.2f} hours")

        print(f"\nBonus Hours: Loaded {len(breakdown_list)} sheets with bonus data")
        total_all_sheets = sum(item['bonus_mhr'] for item in breakdown_list)
        print(f"Bonus Hours: Total across all sheets: {total_all_sheets:.2f} hours")

        return total_bonus_dict, breakdown_list

    except Exception as e:
        print(f"ERROR loading bonus hours file: {e}")
        import traceback
        traceback.print_exc()
        return {}, []


def get_bonus_hours(ac_type, wp_type, bonus_lookup):
    """
    Look up total bonus hours for given ac_type and wp_type.

    Args:
        ac_type: Aircraft type
        wp_type: Work package type
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        float: Total bonus hours from all sheets (0.0 if not found)
    """
    if not bonus_lookup:
        return 0.0

    if ac_type is None or wp_type is None:
        print(f"WARNING: ac_type or wp_type is None, cannot look up bonus hours")
        return 0.0

    if ac_type not in bonus_lookup:
        print(f"Info: ac_type '{ac_type}' not found in bonus hours lookup")
        return 0.0

    if wp_type not in bonus_lookup[ac_type]:
        print(f"Info: wp_type '{wp_type}' not found for ac_type '{ac_type}'")
        return 0.0

    return bonus_lookup[ac_type][wp_type]


def apply_bonus_hours(df, ac_type, wp_type, bonus_lookup):
    """
    Apply bonus hours to the DataFrame.
    Adds bonus hours to 'Adjusted Hours' column.

    Args:
        df: DataFrame with 'Adjusted Hours' column
        ac_type: Aircraft type
        wp_type: Work package type
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        DataFrame: Updated DataFrame with bonus hours applied
    """
    if 'Adjusted Hours' not in df.columns:
        print("WARNING: 'Adjusted Hours' column not found, cannot apply bonus hours")
        return df

    # Get total bonus hours for this combination
    bonus_hours = get_bonus_hours(ac_type, wp_type, bonus_lookup)

    if bonus_hours > 0:
        print(f"\nApplying total bonus hours: +{bonus_hours:.2f} hours")
        print(f"  (ac_type='{ac_type}', wp_type='{wp_type}')")
        df['Adjusted Hours'] = df['Adjusted Hours'] + bonus_hours
    else:
        print(f"\nNo bonus hours found for ac_type='{ac_type}', wp_type='{wp_type}'")

    return df