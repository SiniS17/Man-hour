"""
Fixed A Extractor Module
CRITICAL FIX: Bonus hours should NOT be added to every row
Instead, they are tracked separately and only added to the final total
"""

import pandas as pd
import os
from utils.logger import get_logger
from core.config import (A_COLUMN, REFERENCE_FOLDER, BONUS_HOURS_FILE,
                         AC_TYPE_FILE, AC_TYPE_REGISTRATION_COLUMN,
                         AC_TYPE_TYPE_COLUMN, BONUS_1_COLUMN, BONUS_2_COLUMN,
                         AIRCRAFT_CODE_COLUMN, PRODUCT_CODE_COLUMN)

# Get module-specific logger
logger = get_logger(module_name="a_extractor")


def extract_ac_name_and_wp_type(value):
    """
    Extract ac_name and wp_type from a column value.

    Args:
        value: String value from column A

    Returns:
        tuple: (ac_name, wp_type)
    """
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
    """
    Load aircraft type lookup table from REFERENCE folder.

    Returns:
        dict: Dictionary mapping {ac_name (registration): ac_type (type)}
    """
    ac_type_file = os.path.join(REFERENCE_FOLDER, AC_TYPE_FILE)

    if not os.path.exists(ac_type_file):
        logger.warning(f"Aircraft type lookup file not found at {ac_type_file}")
        logger.warning("Cannot determine aircraft type")
        return {}

    try:
        df = pd.read_excel(ac_type_file, engine='openpyxl')

        required_cols = [AC_TYPE_TYPE_COLUMN, AC_TYPE_REGISTRATION_COLUMN]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            logger.warning(f"Aircraft type file missing columns: {missing_cols}")
            logger.debug(f"Available columns: {list(df.columns)}")
            return {}

        # Build lookup dictionary
        ac_lookup = {}
        for idx, row in df.iterrows():
            regis = str(row[AC_TYPE_REGISTRATION_COLUMN]).strip()
            ac_type = str(row[AC_TYPE_TYPE_COLUMN]).strip()
            ac_lookup[regis] = ac_type

        logger.info(f"Loaded aircraft type lookup: {len(ac_lookup)} entries")
        return ac_lookup

    except Exception as e:
        logger.error(f"Error loading aircraft type file: {e}")
        return {}


def get_ac_type_from_name(ac_name, ac_lookup):
    """
    Look up aircraft type from aircraft name (registration).

    Args:
        ac_name: Aircraft registration/name
        ac_lookup: Dictionary from load_ac_type_lookup()

    Returns:
        str: Aircraft type, or None if not found
    """
    if not ac_lookup or not ac_name:
        return None

    return ac_lookup.get(ac_name)


def extract_from_dataframe(df):
    """
    Extract ac_name and wp_type from the first row of column A in dataframe.
    Then look up the ac_type from the aircraft type lookup table.

    Args:
        df: Input DataFrame

    Returns:
        tuple: (ac_type, wp_type, ac_name)
    """
    if A_COLUMN not in df.columns:
        logger.warning(f"Column '{A_COLUMN}' not found in file")
        logger.debug(f"Available columns: {list(df.columns)}")
        return None, None, None

    if len(df) == 0:
        logger.warning(f"DataFrame is empty, cannot extract from column '{A_COLUMN}'")
        return None, None, None

    # Get the first value from column A
    first_value = df[A_COLUMN].iloc[0]

    # Extract ac_name and wp_type
    ac_name, wp_type = extract_ac_name_and_wp_type(first_value)

    logger.info(f"Extracted from '{A_COLUMN}': ac_name='{ac_name}', wp_type='{wp_type}'")

    # Load aircraft type lookup
    ac_lookup = load_ac_type_lookup()

    # Look up ac_type from ac_name
    ac_type = get_ac_type_from_name(ac_name, ac_lookup)

    if ac_type:
        logger.info(f"Looked up ac_type: '{ac_type}' for ac_name '{ac_name}'")
    else:
        logger.warning(f"Could not find ac_type for ac_name '{ac_name}'")

    return ac_type, wp_type, ac_name


def load_bonus_hours_lookup():
    """
    Load bonus hours from ALL sheets in the bonus hours file.
    Filters by IsActive column if present (only includes TRUE values).

    Returns:
        dict: Nested dictionary {wp_type: {ac_type: total_bonus_hours}}
    """
    bonus_file_path = os.path.join(REFERENCE_FOLDER, BONUS_HOURS_FILE)

    if not os.path.exists(bonus_file_path):
        logger.info(f"Bonus hours file not found at {bonus_file_path}")
        logger.info("No bonus hours will be applied")
        return {}

    try:
        excel_file = pd.ExcelFile(bonus_file_path, engine='openpyxl')
        bonus_lookup = {}

        logger.info("")
        logger.info(f"Loading bonus hours from {BONUS_HOURS_FILE}...")
        logger.info(f"Found {len(excel_file.sheet_names)} sheets to process")
        logger.debug(f"Column mapping: Aircraft='{AIRCRAFT_CODE_COLUMN}', Product='{PRODUCT_CODE_COLUMN}', Bonus1='{BONUS_1_COLUMN}', Bonus2='{BONUS_2_COLUMN}'")

        total_rows_processed = 0
        total_rows_skipped_inactive = 0

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            logger.debug(f"Processing sheet '{sheet_name}'...")

            rows_before_filter = len(df)

            rows_before_filter = len(df)

            # Check for required columns
            missing_cols = []
            if AIRCRAFT_CODE_COLUMN not in df.columns:
                missing_cols.append(AIRCRAFT_CODE_COLUMN)
            if PRODUCT_CODE_COLUMN not in df.columns:
                missing_cols.append(PRODUCT_CODE_COLUMN)

            # Check for at least one bonus column
            has_bonus_1 = BONUS_1_COLUMN in df.columns
            has_bonus_2 = BONUS_2_COLUMN in df.columns

            if not has_bonus_1 and not has_bonus_2:
                missing_cols.append(f"{BONUS_1_COLUMN} or {BONUS_2_COLUMN}")

            if missing_cols:
                logger.warning(f"Sheet '{sheet_name}' missing columns: {missing_cols}")
                logger.debug(f"Available columns: {list(df.columns)}")
                continue

            # FILTER BY IsActive COLUMN if it exists
            has_isactive = 'IsActive' in df.columns
            if has_isactive:
                logger.debug(f"Found 'IsActive' column in sheet '{sheet_name}' - filtering for TRUE values only")
                df = df[df['IsActive'] == True].copy()
                rows_after_filter = len(df)
                rows_skipped = rows_before_filter - rows_after_filter
                total_rows_skipped_inactive += rows_skipped
                logger.debug(f"  Active rows: {rows_after_filter}, Skipped (inactive): {rows_skipped}")
            else:
                logger.debug(f"No 'IsActive' column in sheet '{sheet_name}' - processing all rows")

            # Process each row
            rows_in_sheet = 0

            for idx, row in df.iterrows():
                ac_type = str(row[AIRCRAFT_CODE_COLUMN]).strip()

                if pd.isna(row[AIRCRAFT_CODE_COLUMN]) or ac_type.lower() in ['nan', '', 'none']:
                    continue

                wp_type = str(row[PRODUCT_CODE_COLUMN]).strip()

                if pd.isna(row[PRODUCT_CODE_COLUMN]) or wp_type.lower() in ['nan', '', 'none']:
                    continue

                # Sum bonus hours
                total_bonus = 0.0
                if has_bonus_1 and pd.notna(row[BONUS_1_COLUMN]):
                    try:
                        total_bonus += float(row[BONUS_1_COLUMN])
                    except (ValueError, TypeError):
                        pass

                if has_bonus_2 and pd.notna(row[BONUS_2_COLUMN]):
                    try:
                        total_bonus += float(row[BONUS_2_COLUMN])
                    except (ValueError, TypeError):
                        pass

                # Store
                if wp_type not in bonus_lookup:
                    bonus_lookup[wp_type] = {}

                bonus_lookup[wp_type][ac_type] = total_bonus
                rows_in_sheet += 1
                total_rows_processed += 1

            logger.debug(f"Loaded {rows_in_sheet} rows from sheet '{sheet_name}'")

        # Summary
        logger.info(f"✓ Successfully loaded bonus hours:")
        logger.info(f"  - Total rows processed: {total_rows_processed}")
        if total_rows_skipped_inactive > 0:
            logger.info(f"  - Rows skipped (inactive): {total_rows_skipped_inactive}")
        logger.info(f"  - Product codes found: {len(bonus_lookup)}")
        for wp_type in sorted(bonus_lookup.keys()):
            logger.debug(f"    • {wp_type}: {len(bonus_lookup[wp_type])} aircraft types")
        logger.info("")

        return bonus_lookup

    except Exception as e:
        logger.error(f"Error loading bonus hours file: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {}


def get_bonus_hours(ac_type, wp_type, bonus_lookup):
    """
    Look up bonus hours for given ac_type and wp_type.

    IMPORTANT: This returns the TOTAL bonus for the entire workpack,
    NOT a per-row bonus. It should be added to the final total ONCE.

    Args:
        ac_type: Aircraft type
        wp_type: Check/product type
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        float: Bonus hours (0.0 if not found)
    """
    if not bonus_lookup:
        return 0.0

    if ac_type is None:
        logger.warning("ac_type is None, cannot look up bonus hours")
        return 0.0

    if wp_type not in bonus_lookup:
        logger.info(f"wp_type '{wp_type}' not found in bonus hours lookup")
        logger.debug(f"Available wp_types: {sorted(list(bonus_lookup.keys()))}")
        return 0.0

    if ac_type not in bonus_lookup[wp_type]:
        logger.info(f"ac_type '{ac_type}' not found for wp_type '{wp_type}'")
        logger.debug(f"Available ac_types for '{wp_type}': {sorted(list(bonus_lookup[wp_type].keys()))}")
        return 0.0

    bonus = bonus_lookup[wp_type][ac_type]
    logger.info(f"✓ Found bonus hours: {bonus:.2f} hours for ac_type='{ac_type}', wp_type='{wp_type}'")
    logger.info(f"  NOTE: This is a WORKPACK-LEVEL bonus, added ONCE to the final total")
    return bonus


def get_bonus_breakdown_by_source(ac_type, wp_type):
    """
    Get breakdown of bonus hours by source sheet.
    Only includes active records (IsActive = TRUE if column exists).

    Args:
        ac_type: Aircraft type
        wp_type: Check/product type

    Returns:
        dict: {sheet_name: bonus_hours}
    """
    bonus_file_path = os.path.join(REFERENCE_FOLDER, BONUS_HOURS_FILE)

    if not os.path.exists(bonus_file_path):
        return {}

    try:
        excel_file = pd.ExcelFile(bonus_file_path, engine='openpyxl')
        breakdown = {}

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            # Check if required columns exist
            if AIRCRAFT_CODE_COLUMN not in df.columns or PRODUCT_CODE_COLUMN not in df.columns:
                continue

            # FILTER BY IsActive if column exists
            if 'IsActive' in df.columns:
                df = df[df['IsActive'] == True].copy()

            has_bonus_1 = BONUS_1_COLUMN in df.columns
            has_bonus_2 = BONUS_2_COLUMN in df.columns

            if not has_bonus_1 and not has_bonus_2:
                continue

            # Find matching row
            for idx, row in df.iterrows():
                row_ac_type = str(row[AIRCRAFT_CODE_COLUMN]).strip()
                row_wp_type = str(row[PRODUCT_CODE_COLUMN]).strip()

                if row_ac_type == ac_type and row_wp_type == wp_type:
                    total_bonus = 0.0
                    if has_bonus_1 and pd.notna(row[BONUS_1_COLUMN]):
                        try:
                            total_bonus += float(row[BONUS_1_COLUMN])
                        except:
                            pass
                    if has_bonus_2 and pd.notna(row[BONUS_2_COLUMN]):
                        try:
                            total_bonus += float(row[BONUS_2_COLUMN])
                        except:
                            pass

                    if total_bonus > 0:
                        breakdown[sheet_name] = total_bonus
                    break

        return breakdown

    except Exception as e:
        logger.warning(f"Could not get bonus breakdown: {e}")
        return {}


def apply_bonus_hours(df, ac_type, wp_type, bonus_lookup):
    """
    REMOVED: Do NOT add bonus to every row!

    Bonus hours are WORKPACK-LEVEL additions, not row-level.
    They should only be added to the final total ONCE.

    This function now does NOTHING and is kept for backward compatibility.
    The bonus is handled in the data_processor total calculation.

    Args:
        df: DataFrame with 'Adjusted Hours' column
        ac_type: Aircraft type
        wp_type: Check value
        bonus_lookup: Dictionary from load_bonus_hours_lookup()

    Returns:
        DataFrame: UNCHANGED DataFrame (bonus NOT applied to rows)
    """
    logger.info("apply_bonus_hours() called - bonus is now handled at total calculation level")
    logger.info("NOT adding bonus to individual rows (would multiply bonus by number of rows)")

    # Return DataFrame unchanged
    return df