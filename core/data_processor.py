"""
Data Processor Module
Core processing logic for workpack data analysis
REFACTORED: Now uses centralized logging system
"""

import pandas as pd
import os
from datetime import datetime
from utils.time_utils import convert_planned_mhrs, hours_to_hhmm
from utils.validation import validate_required_columns
from utils.logger import get_logger, WorkpackLogger
from core.config import (SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN,
                         HIGH_MHRS_HOURS, RANDOM_SAMPLE_SIZE,
                         ENABLE_SPECIAL_CODE, SPECIAL_CODE_COLUMN,
                         ENABLE_TOOL_CONTROL, REFERENCE_EO_PREFIX, SPECIAL_TYPE_COLUMN)
from core.id_extractor import extract_task_id
from core.data_loader import load_input_dataframe, extract_workpack_dates
from features.special_code import (calculate_special_code_distribution,
                                   calculate_special_code_per_day,
                                   validate_special_code_column)
from features.type_coefficient import (load_type_coefficient_lookup, apply_type_coefficients,
                                       calculate_type_coefficient_breakdown, calculate_total_type_coefficient_hours)
from features.a_extractor import (extract_from_dataframe, load_bonus_hours_lookup,
                                  apply_bonus_hours, get_bonus_hours, get_bonus_breakdown_by_source)

# Import tool control module if enabled
if ENABLE_TOOL_CONTROL:
    from features.tool_control import process_tool_control


def process_data(input_file_path, reference_data):
    """
    Main data processing function. This will extract task IDs, validate man-hours,
    and generate a report.

    Args:
        input_file_path (str): Path to the input Excel file
        reference_data (dict): Dictionary containing 'task_ids' and 'eo_ids' sets

    Returns:
        dict: Dictionary with structured data for Excel output
    """
    # Initialize file-specific logger
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    logger = get_logger(base_filename=base_filename)

    logger.info("="*80)
    logger.info("STARTING DATA PROCESSING")
    logger.info("="*80)
    logger.info(f"File: {input_file_path}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Load the uploaded file
    df = load_input_dataframe(input_file_path)

    logger.info("INITIAL DATA CHECK")
    logger.info("-"*80)
    logger.info(f"Total rows loaded: {len(df)}")
    logger.debug(f"Columns: {list(df.columns)}")

    if SPECIAL_TYPE_COLUMN in df.columns:
        logger.info(f"✓ Special type column '{SPECIAL_TYPE_COLUMN}' found!")
        unique_types = df[SPECIAL_TYPE_COLUMN].dropna().unique()
        logger.info(f"Unique special types: {list(unique_types)}")
    else:
        logger.info(f"✗ Special type column '{SPECIAL_TYPE_COLUMN}' NOT FOUND")
    logger.info("")

    # Extract workpack dates
    workpack_info = extract_workpack_dates(df)

    # Extract ac_type and wp_type from column A
    ac_type, wp_type, ac_name = extract_from_dataframe(df)

    logger.info("EXTRACTED INFO")
    logger.info("-"*80)
    logger.info(f"ac_type: {ac_type}")
    logger.info(f"wp_type: {wp_type}")
    logger.info(f"ac_name: {ac_name}")
    logger.info("")

    # Load lookup tables
    bonus_lookup = load_bonus_hours_lookup()
    type_coeff_lookup = load_type_coefficient_lookup()

    # Build list of required columns based on configuration
    required_columns = [SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN]

    # Validate special code configuration
    enable_special_code_processing = False
    if ENABLE_SPECIAL_CODE:
        is_valid, error_msg = validate_special_code_column(df, SPECIAL_CODE_COLUMN)
        if not is_valid:
            logger.warning(f"{error_msg}")
            logger.warning("Proceeding without special code analysis...")
        else:
            required_columns.append(SPECIAL_CODE_COLUMN)
            enable_special_code_processing = True

    # Check for required columns
    base_required = [SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN]
    validate_required_columns(df, base_required, input_file_path)

    # Check tool availability if enabled (processes independently)
    tool_control_issues = pd.DataFrame()
    if ENABLE_TOOL_CONTROL:
        from core.config import SEQ_MAPPINGS, SEQ_ID_MAPPINGS
        tool_control_issues = process_tool_control(input_file_path, SEQ_MAPPINGS, SEQ_ID_MAPPINGS)

    # Convert "Planned Mhrs" (in minutes) to base hours
    df['Base Hours'] = df[PLANNED_MHRS_COLUMN].apply(convert_planned_mhrs)

    logger.info("AFTER BASE HOURS CALCULATION")
    logger.info("-"*80)
    logger.info(f"Total Base Hours (all rows): {df['Base Hours'].sum():.2f}")
    logger.info("")

    # Apply type coefficients based on special type column (to ALL rows)
    df = apply_type_coefficients(df, ac_type, wp_type, type_coeff_lookup)

    logger.info("AFTER TYPE COEFFICIENT APPLICATION")
    logger.info("-"*80)
    logger.info(f"Total Base Hours: {df['Base Hours'].sum():.2f}")
    logger.info(f"Total Adjusted Hours: {df['Adjusted Hours'].sum():.2f}")
    logger.info(f"Difference: {(df['Adjusted Hours'].sum() - df['Base Hours'].sum()):.2f}")
    logger.info("")

    # Extract task IDs and check flags
    task_id_data = df.apply(extract_task_id, axis=1)
    df['Task ID'] = task_id_data.apply(lambda x: x[0])
    df['Should Check Reference'] = task_id_data.apply(lambda x: x[1])
    df['Should Process'] = task_id_data.apply(lambda x: x[2])

    # Keep a copy of the original data (before deduplication) for type coefficient calculation
    df_original_for_coeff = df[df['Should Process'] == True].copy()

    logger.info("BEFORE DEDUPLICATION")
    logger.info("-"*80)
    logger.info(f"Rows to process: {len(df_original_for_coeff)}")
    logger.info(f"Total Base Hours: {df_original_for_coeff['Base Hours'].sum():.2f}")
    logger.info(f"Total Adjusted Hours: {df_original_for_coeff['Adjusted Hours'].sum():.2f}")
    logger.info("")

    # Filter out rows that should not be processed (ignore mode)
    df_processed = df[df['Should Process'] == True].copy()

    # IMPORTANT: Keep only the FIRST occurrence of each SEQ to avoid duplicate man-hour counting
    df_processed = df_processed.drop_duplicates(subset=[SEQ_NO_COLUMN], keep='first')

    logger.info("AFTER DEDUPLICATION")
    logger.info("-"*80)
    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Rows to process (after removing duplicates): {len(df_processed)}")
    logger.info(f"Rows ignored: {len(df) - len(df_processed)}")
    logger.info(f"Total Base Hours (deduplicated): {df_processed['Base Hours'].sum():.2f}")
    logger.info(f"Total Adjusted Hours (deduplicated): {df_processed['Adjusted Hours'].sum():.2f}")
    logger.info("")

    # Debugging: Log rows with None task IDs
    none_task_ids = df_processed[df_processed['Task ID'].isna()]
    if not none_task_ids.empty:
        logger.debug(f"Rows with None Task IDs:")
        for idx, row in none_task_ids.iterrows():
            logger.debug(f"  SEQ {row[SEQ_NO_COLUMN]}: {row[TITLE_COLUMN]}")
        logger.debug("")

    # Calculate total base hours
    total_base_mhrs = df_processed['Base Hours'].sum()

    # Calculate type coefficient breakdown
    type_coeff_breakdown = calculate_type_coefficient_breakdown(df_original_for_coeff, df_processed)
    type_coefficient_hours = calculate_total_type_coefficient_hours(df_original_for_coeff, df_processed)

    # Get the bonus hours amount for this aircraft/check combination
    bonus_hours = get_bonus_hours(ac_type, wp_type, bonus_lookup)

    # Get bonus breakdown by source
    bonus_breakdown = get_bonus_breakdown_by_source(ac_type, wp_type)

    logger.info("BONUS BREAKDOWN")
    logger.info("-"*80)
    logger.debug(f"Bonus from files: {bonus_breakdown}")
    logger.debug(f"Type coeff breakdown: {type_coeff_breakdown}")
    logger.info("")

    # Combine bonus breakdown with type coefficient breakdown
    combined_bonus_breakdown = {}

    # Add regular bonus hours
    if bonus_breakdown:
        for source, hours in bonus_breakdown.items():
            if hours > 0:
                combined_bonus_breakdown[source] = hours

    # Add type coefficient as bonus items
    if type_coeff_breakdown:
        for special_type, additional_hours in type_coeff_breakdown.items():
            if abs(additional_hours) > 0.01:
                combined_bonus_breakdown[f"Type Coefficient ({special_type})"] = additional_hours

    logger.debug(f"Combined: {combined_bonus_breakdown}")
    logger.info("")

    # Calculate total additional hours (bonus + type coefficient)
    total_additional_hours = bonus_hours + type_coefficient_hours

    logger.info("TOTALS BEFORE APPLYING BONUS")
    logger.info("-"*80)
    logger.info(f"Bonus hours: {bonus_hours:.2f}")
    logger.info(f"Type coefficient hours: {type_coefficient_hours:.2f}")
    logger.info(f"Total additional: {total_additional_hours:.2f}")
    logger.info("")

    # Apply bonus hours to dataframe
    df_processed = apply_bonus_hours(df_processed, ac_type, wp_type, bonus_lookup)

    # Calculate total man-hours AFTER all adjustments
    total_mhrs = df_processed['Adjusted Hours'].sum()

    logger.info("FINAL TOTALS")
    logger.info("-"*80)
    logger.info(f"Total Base: {total_base_mhrs:.2f}")
    logger.info(f"Total Additional: {total_additional_hours:.2f}")
    logger.info(f"Total Man-Hours: {total_mhrs:.2f}")
    logger.debug(f"Calculation check: {total_base_mhrs:.2f} + {total_additional_hours:.2f} = {total_base_mhrs + total_additional_hours:.2f}")
    logger.info("")

    # Identify high man-hours tasks
    high_mhrs_tasks = df_processed[df_processed['Adjusted Hours'] > HIGH_MHRS_HOURS]

    # Check for new task IDs
    new_task_ids_with_seq = identify_new_task_ids(
        df_processed,
        reference_data['task_ids'],
        reference_data['eo_ids']
    )

    # Generate a random sample for debugging
    sample_size = min(RANDOM_SAMPLE_SIZE, len(df_processed))
    random_sample = df_processed.sample(n=sample_size, random_state=1) if len(df_processed) > 0 else pd.DataFrame()

    # Calculate special code distribution if enabled
    special_code_distribution = None
    special_code_per_day = None
    if enable_special_code_processing:
        special_code_distribution = calculate_special_code_distribution(df_processed)
        special_code_per_day = calculate_special_code_per_day(
            special_code_distribution,
            workpack_info['workpack_days']
        )

    logger.info("="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total Base Man-Hours: {hours_to_hhmm(total_base_mhrs)}")
    logger.info(f"Type Coefficient Additional Hours: {hours_to_hhmm(type_coefficient_hours)}")
    if bonus_hours > 0:
        logger.info(f"Bonus Hours: +{hours_to_hhmm(bonus_hours)}")
    logger.info(f"Total Additional Hours: {hours_to_hhmm(total_additional_hours)}")
    logger.info(f"Final Total: {hours_to_hhmm(total_mhrs)}")
    logger.info("="*80)
    logger.info("")

    # Write debug sample to log
    write_debug_sample_to_log(logger, random_sample, enable_special_code_processing)

    # Close the file-specific logger
    WorkpackLogger().close_file_logger(base_filename)

    # Return structured data dictionary
    return {
        'total_mhrs': total_mhrs,
        'total_base_mhrs': total_base_mhrs,
        'total_additional_hours': total_additional_hours,
        'bonus_breakdown': combined_bonus_breakdown,
        'total_mhrs_hhmm': hours_to_hhmm(total_mhrs),
        'total_base_mhrs_hhmm': hours_to_hhmm(total_base_mhrs),
        'ac_type': ac_type,
        'ac_name': ac_name,
        'wp_type': wp_type,
        'special_code_distribution': special_code_distribution,
        'special_code_per_day': special_code_per_day,
        'workpack_days': workpack_info['workpack_days'],
        'start_date': workpack_info['start_date'],
        'end_date': workpack_info['end_date'],
        'enable_special_code': enable_special_code_processing,
        'enable_tool_control': ENABLE_TOOL_CONTROL,
        'tool_control_issues': tool_control_issues,
        'high_mhrs_tasks': high_mhrs_tasks,
        'new_task_ids_with_seq': new_task_ids_with_seq,
        'debug_sample': random_sample,
        'high_mhrs_threshold': HIGH_MHRS_HOURS
    }


def identify_new_task_ids(df_processed, reference_task_ids, reference_eo_ids):
    """
    Identify task IDs that are not in the reference data.

    Args:
        df_processed (pd.DataFrame): Processed DataFrame
        reference_task_ids (set): Set of reference task IDs
        reference_eo_ids (set): Set of reference EO IDs

    Returns:
        pd.DataFrame: DataFrame with SEQ and Task ID columns for new IDs
    """
    # Check only rows that should be checked
    rows_to_check = df_processed[df_processed['Should Check Reference'] == True].copy()

    # Separate EO and Task IDs
    rows_to_check['Is_EO'] = rows_to_check['Task ID'].astype(str).str.startswith(REFERENCE_EO_PREFIX)

    # Check EO IDs against EO reference
    eo_rows = rows_to_check[rows_to_check['Is_EO'] == True]
    new_eo_rows = eo_rows[~eo_rows['Task ID'].isin(reference_eo_ids)]

    # Check Task IDs against Task reference
    task_rows = rows_to_check[rows_to_check['Is_EO'] == False]
    new_task_rows = task_rows[~task_rows['Task ID'].isin(reference_task_ids)]

    # Combine new IDs from both sources
    new_task_ids_with_seq = pd.concat([new_eo_rows, new_task_rows])[[SEQ_NO_COLUMN, 'Task ID']].copy()

    return new_task_ids_with_seq


def write_debug_sample_to_log(logger, debug_df, enable_special_code):
    """
    Write the debug sample section to the log file.

    Args:
        logger: Logger instance
        debug_df (pd.DataFrame): Debug sample DataFrame
        enable_special_code (bool): Whether special code is enabled
    """
    logger.info("")
    logger.info("="*80)
    logger.info("DEBUG SAMPLE REPORT")
    logger.info("="*80)

    if len(debug_df) == 0:
        logger.info("No data to display (all rows were ignored)")
        return

    logger.info(f"Random Sample ({len(debug_df)} Rows):")
    logger.info("-"*120)

    if enable_special_code:
        logger.info(f"| {SEQ_NO_COLUMN:<8} | Special Code | Task ID          | Type Coeff | Base Mhrs | Adjusted Mhrs |")
        logger.info("-"*120)

        for idx, row in debug_df.iterrows():
            seq_no = str(row[SEQ_NO_COLUMN])
            special_code = str(row.get('Special code', 'N/A')) if pd.notna(row.get('Special code')) else "N/A"
            special_code = special_code[:12]
            task_id = str(row['Task ID'])[:16]
            type_coefficient = row.get('Type Coefficient', 1.0)
            base_hours = row.get('Base Hours', 0)
            adjusted_hours = row.get('Adjusted Hours', 0)
            base_time_hhmm = hours_to_hhmm(base_hours)
            adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

            logger.info(
                f"| {seq_no:<8} | {special_code:<12} | {task_id:<16} | {type_coefficient:<10.2f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |")
    else:
        logger.info(
            f"| {SEQ_NO_COLUMN:<8} | {TITLE_COLUMN[:30]:<30} | Task ID          | Type Coeff | Base Mhrs | Adjusted Mhrs |")
        logger.info("-"*125)

        for idx, row in debug_df.iterrows():
            seq_no = str(row[SEQ_NO_COLUMN])
            title = str(row[TITLE_COLUMN])[:30]
            task_id = str(row['Task ID'])[:16]
            type_coefficient = row.get('Type Coefficient', 1.0)
            base_hours = row.get('Base Hours', 0)
            adjusted_hours = row.get('Adjusted Hours', 0)
            base_time_hhmm = hours_to_hhmm(base_hours)
            adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

            logger.info(
                f"| {seq_no:<8} | {title:<30} | {task_id:<16} | {type_coefficient:<10.2f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |")

    logger.info("-"*120)