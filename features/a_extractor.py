"""
A Extractor Module
Handles aircraft info and bonus hours extraction
UPDATED: Filters bonus hours by IsActive column
"""

import pandas as pd
import os
from utils.logger import get_logger
from core.config import (A_COLUMN, REFERENCE_FOLDER, BONUS_HOURS_FILE,
                         AC_TYPE_FILE, AC_TYPE_REGISTRATION_COLUMN,
                         AC_TYPE_TYPE_COLUMN, BONUS_1_COLUMN, BONUS_2_COLUMN,
                         AIRCRAFT_CODE_COLUMN, PRODUCT_CODE_COLUMN,
                         BONUS_ISACTIVE_COLUMN)

logger = get_logger(module_name="a_extractor")


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
        logger.warning(f"Aircraft type lookup file not found at {ac_type_file}")
        return {}

    try:
        df = pd.read_excel(ac_type_file, engine='openpyxl')

        required_cols = [AC_TYPE_TYPE_COLUMN, AC_TYPE_REGISTRATION_COLUMN]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            logger.warning(f"Aircraft type file missing columns: {missing_cols}")
            return {}

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
    """Look up aircraft type from aircraft name."""
    if not ac_lookup or not ac_name:
        return None
    return ac_lookup.get(ac_name)


def extract_from_dataframe(df):
    """Extract ac_type, wp_type, and ac_name from DataFrame."""
    if A_COLUMN not in df.columns:
        logger.warning(f"Column '{A_COLUMN}' not found in file")
        return None, None, None

    if len(df) == 0:
        logger.warning(f"DataFrame is empty")
        return None, None, None

    first_value = df[A_COLUMN].iloc[0]
    ac_name, wp_type = extract_ac_name_and_wp_type(first_value)

    logger.info(f"Extracted from '{A_COLUMN}': ac_name='{ac_name}', wp_type='{wp_type}'")

    ac_lookup = load_ac_type_lookup()
    ac_type = get_ac_type_from_name(ac_name, ac_lookup)

    if ac_type:
        logger.info(f"Looked up ac_type: '{ac_type}' for ac_name '{ac_name}'")
    else:
        logger.warning(f"Could not find ac_type for ac_name '{ac_name}'")

    return ac_type, wp_type, ac_name


"""
Fix for features/a_extractor.py - load_bonus_hours_lookup()
Bug: Bonus hours from multiple sheets are overwriting instead of accumulating
Solution: Add bonus hours instead of overwriting them
"""

def load_bonus_hours_lookup():
    """
    Load bonus hours from ALL sheets in the bonus hours file.
    ONLY includes rows where IsActive = TRUE (or if IsActive column doesn't exist).
    ACCUMULATES bonus hours from multiple sheets for the same ac_type/wp_type combination.
    """
    bonus_file_path = os.path.join(REFERENCE_FOLDER, BONUS_HOURS_FILE)

    if not os.path.exists(bonus_file_path):
        logger.info(f"Bonus hours file not found at {bonus_file_path}")
        return {}

    try:
        excel_file = pd.ExcelFile(bonus_file_path, engine='openpyxl')
        bonus_lookup = {}

        logger.info("")
        logger.info(f"Loading bonus hours from {BONUS_HOURS_FILE}...")
        logger.info(f"Found {len(excel_file.sheet_names)} sheets to process")

        total_rows_processed = 0
        total_rows_skipped_inactive = 0

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            logger.debug(f"Processing sheet '{sheet_name}'...")

            rows_before_filter = len(df)

            # Check for required columns
            missing_cols = []
            if AIRCRAFT_CODE_COLUMN not in df.columns:
                missing_cols.append(AIRCRAFT_CODE_COLUMN)
            if PRODUCT_CODE_COLUMN not in df.columns:
                missing_cols.append(PRODUCT_CODE_COLUMN)

            has_bonus_1 = BONUS_1_COLUMN in df.columns
            has_bonus_2 = BONUS_2_COLUMN in df.columns

            if not has_bonus_1 and not has_bonus_2:
                missing_cols.append(f"{BONUS_1_COLUMN} or {BONUS_2_COLUMN}")

            if missing_cols:
                logger.warning(f"Sheet '{sheet_name}' missing columns: {missing_cols}")
                continue

            # FILTER BY IsActive = TRUE (if column exists)
            has_isactive = BONUS_ISACTIVE_COLUMN in df.columns
            if has_isactive:
                logger.debug(f"Found '{BONUS_ISACTIVE_COLUMN}' column - filtering for TRUE values only")
                # Filter for TRUE values
                df = df[df[BONUS_ISACTIVE_COLUMN] == True].copy()
                rows_after_filter = len(df)
                rows_skipped = rows_before_filter - rows_after_filter
                total_rows_skipped_inactive += rows_skipped
                logger.debug(f"  Active rows: {rows_after_filter}, Skipped (inactive): {rows_skipped}")
            else:
                logger.debug(f"No '{BONUS_ISACTIVE_COLUMN}' column - processing all rows")

            # Process each active row
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

                # FIXED: ACCUMULATE instead of OVERWRITE
                if wp_type not in bonus_lookup:
                    bonus_lookup[wp_type] = {}

                if ac_type not in bonus_lookup[wp_type]:
                    bonus_lookup[wp_type][ac_type] = 0.0  # Initialize to 0

                # ADD to existing value instead of overwriting
                bonus_lookup[wp_type][ac_type] += total_bonus

                rows_in_sheet += 1
                total_rows_processed += 1

            logger.debug(f"Loaded {rows_in_sheet} active rows from sheet '{sheet_name}'")

        # Summary
        logger.info(f"✓ Successfully loaded bonus hours:")
        logger.info(f"  - Total active rows processed: {total_rows_processed}")
        if total_rows_skipped_inactive > 0:
            logger.info(f"  - Rows skipped ({BONUS_ISACTIVE_COLUMN}=FALSE): {total_rows_skipped_inactive}")
        logger.info(f"  - Product codes found: {len(bonus_lookup)}")
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
    Returns 0.0 if not found OR if the record was IsActive=FALSE.
    """
    if not bonus_lookup:
        return 0.0

    if ac_type is None:
        logger.warning("ac_type is None, cannot look up bonus hours")
        return 0.0

    if wp_type not in bonus_lookup:
        logger.info(f"wp_type '{wp_type}' not found in bonus hours lookup")
        return 0.0

    if ac_type not in bonus_lookup[wp_type]:
        logger.info(f"ac_type '{ac_type}' not found for wp_type '{wp_type}'")
        return 0.0

    bonus = bonus_lookup[wp_type][ac_type]
    logger.info(f"✓ Found bonus hours: {bonus:.2f} hours (ac_type='{ac_type}', wp_type='{wp_type}')")
    logger.info(f"  Source: This is the TOTAL from all active sheets in '{BONUS_HOURS_FILE}'")
    return bonus


def get_bonus_breakdown_by_source(ac_type, wp_type, file_logger=None):
    """
    Get breakdown of bonus hours by source sheet.
    Only includes rows where IsActive = TRUE.
    Returns dict with detailed source information.

    Args:
        ac_type: Aircraft type code
        wp_type: Work package type
        file_logger: Optional file-specific logger (if None, uses module logger)
    """
    bonus_file_path = os.path.join(REFERENCE_FOLDER, BONUS_HOURS_FILE)

    if not os.path.exists(bonus_file_path):
        return {}

    # Use provided logger or fall back to module logger
    if file_logger is None:
        file_logger = get_logger(module_name="a_extractor")

    try:
        excel_file = pd.ExcelFile(bonus_file_path, engine='openpyxl')
        breakdown = {}

        file_logger.info("")
        file_logger.info("="*80)
        file_logger.info("BONUS HOURS SOURCE DETAILS")
        file_logger.info("="*80)
        file_logger.info(f"Looking up: ac_type='{ac_type}', wp_type='{wp_type}'")
        file_logger.info(f"File: {BONUS_HOURS_FILE}")
        file_logger.info("")

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            if AIRCRAFT_CODE_COLUMN not in df.columns or PRODUCT_CODE_COLUMN not in df.columns:
                continue

            # Store original row count before filtering
            original_row_count = len(df)

            # FILTER BY IsActive = TRUE (if column exists)
            has_isactive = BONUS_ISACTIVE_COLUMN in df.columns
            if has_isactive:
                df_filtered = df[df[BONUS_ISACTIVE_COLUMN] == True].copy()
                skipped_count = original_row_count - len(df_filtered)
                df = df_filtered
            else:
                skipped_count = 0

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
                    bonus_1_value = 0.0
                    bonus_2_value = 0.0

                    if has_bonus_1 and pd.notna(row[BONUS_1_COLUMN]):
                        try:
                            bonus_1_value = float(row[BONUS_1_COLUMN])
                            total_bonus += bonus_1_value
                        except:
                            pass

                    if has_bonus_2 and pd.notna(row[BONUS_2_COLUMN]):
                        try:
                            bonus_2_value = float(row[BONUS_2_COLUMN])
                            total_bonus += bonus_2_value
                        except:
                            pass

                    if total_bonus > 0:
                        breakdown[sheet_name] = total_bonus

                        # Log detailed source information
                        file_logger.info(f"Sheet: '{sheet_name}'")
                        file_logger.info(f"  Row: {idx + 2}")  # +2 because Excel is 1-indexed and has header
                        file_logger.info(f"  {AIRCRAFT_CODE_COLUMN}: {row_ac_type}")
                        file_logger.info(f"  {PRODUCT_CODE_COLUMN}: {row_wp_type}")
                        if has_isactive:
                            file_logger.info(f"  {BONUS_ISACTIVE_COLUMN}: {row[BONUS_ISACTIVE_COLUMN]}")
                        if has_bonus_1:
                            file_logger.info(f"  {BONUS_1_COLUMN}: {bonus_1_value:.2f}")
                        if has_bonus_2:
                            file_logger.info(f"  {BONUS_2_COLUMN}: {bonus_2_value:.2f}")
                        file_logger.info(f"  → Total from this sheet: {total_bonus:.2f} hours")
                        if skipped_count > 0:
                            file_logger.info(f"  Note: {skipped_count} row(s) skipped ({BONUS_ISACTIVE_COLUMN}=FALSE)")
                        file_logger.info("")
                    break

        file_logger.info("="*80)
        file_logger.info(f"Total Bonus Hours: {sum(breakdown.values()):.2f}")
        file_logger.info("="*80)
        file_logger.info("")

        return breakdown

    except Exception as e:
        file_logger.warning(f"Could not get bonus breakdown: {e}")
        import traceback
        file_logger.debug(traceback.format_exc())
        return {}