"""
Data Processor Module
Core processing logic for workpack data analysis
"""

import pandas as pd
import os
from datetime import datetime
from utils.time_utils import convert_planned_mhrs, hours_to_hhmm
from utils.validation import validate_required_columns
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
                                       calculate_type_coefficient_breakdown, calculate_total_type_coefficient_hours,
                                       set_logger)
from features.a_extractor import (extract_from_dataframe, load_bonus_hours_lookup,
                                  apply_bonus_hours, get_bonus_hours, get_bonus_breakdown_by_source)
from writers.debug_logger import DebugLogger

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
    # Initialize debug logger
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with DebugLogger(base_filename, timestamp) as logger:
        # Set logger for type_coefficient module
        set_logger(logger)

        logger.log_separator()
        logger.log("STARTING DATA PROCESSING")
        logger.log_separator()
        logger.log(f"File: {input_file_path}")
        logger.log(f"Timestamp: {timestamp}")
        logger.log("")

        # Load the uploaded file
        df = load_input_dataframe(input_file_path)

        logger.log_header("INITIAL DATA CHECK")
        logger.log(f"Total rows loaded: {len(df)}")
        logger.log(f"Columns: {list(df.columns)}")

        if SPECIAL_TYPE_COLUMN in df.columns:
            logger.log(f"✓ Special type column '{SPECIAL_TYPE_COLUMN}' found!")
            unique_types = df[SPECIAL_TYPE_COLUMN].dropna().unique()
            logger.log(f"Unique special types: {list(unique_types)}")
        else:
            logger.log(f"✗ Special type column '{SPECIAL_TYPE_COLUMN}' NOT FOUND")
        logger.log("")

        # Extract workpack dates
        workpack_info = extract_workpack_dates(df)

        # Extract ac_type and wp_type from column A (first row only, since all rows are the same)
        ac_type, wp_type, ac_name = extract_from_dataframe(df)

        logger.log_header("EXTRACTED INFO")
        logger.log(f"ac_type: {ac_type}")
        logger.log(f"wp_type: {wp_type}")
        logger.log(f"ac_name: {ac_name}")
        logger.log("")

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
                logger.log(f"WARNING: {error_msg}")
                logger.log("Proceeding without special code analysis...")
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

        logger.log_header("AFTER BASE HOURS CALCULATION")
        logger.log(f"Total Base Hours (all rows): {df['Base Hours'].sum():.2f}")
        logger.log("")

        # Apply type coefficients based on special type column (to ALL rows)
        df = apply_type_coefficients(df, ac_type, wp_type, type_coeff_lookup)

        logger.log_header("AFTER TYPE COEFFICIENT APPLICATION")
        logger.log(f"Total Base Hours: {df['Base Hours'].sum():.2f}")
        logger.log(f"Total Adjusted Hours: {df['Adjusted Hours'].sum():.2f}")
        logger.log(f"Difference: {(df['Adjusted Hours'].sum() - df['Base Hours'].sum()):.2f}")
        logger.log("")

        # Extract task IDs and check flags
        task_id_data = df.apply(extract_task_id, axis=1)
        df['Task ID'] = task_id_data.apply(lambda x: x[0])
        df['Should Check Reference'] = task_id_data.apply(lambda x: x[1])
        df['Should Process'] = task_id_data.apply(lambda x: x[2])

        # Keep a copy of the original data (before deduplication) for type coefficient calculation
        df_original_for_coeff = df[df['Should Process'] == True].copy()

        logger.log_header("BEFORE DEDUPLICATION")
        logger.log(f"Rows to process: {len(df_original_for_coeff)}")
        logger.log(f"Total Base Hours: {df_original_for_coeff['Base Hours'].sum():.2f}")
        logger.log(f"Total Adjusted Hours: {df_original_for_coeff['Adjusted Hours'].sum():.2f}")
        logger.log("")

        # Filter out rows that should not be processed (ignore mode)
        df_processed = df[df['Should Process'] == True].copy()

        # IMPORTANT: Keep only the FIRST occurrence of each SEQ to avoid duplicate man-hour counting
        df_processed = df_processed.drop_duplicates(subset=[SEQ_NO_COLUMN], keep='first')

        logger.log_header("AFTER DEDUPLICATION")
        logger.log(f"Total rows: {len(df)}")
        logger.log(f"Rows to process (after removing duplicates): {len(df_processed)}")
        logger.log(f"Rows ignored: {len(df) - len(df_processed)}")
        logger.log(f"Total Base Hours (deduplicated): {df_processed['Base Hours'].sum():.2f}")
        logger.log(f"Total Adjusted Hours (deduplicated): {df_processed['Adjusted Hours'].sum():.2f}")
        logger.log("")

        # Debugging: Print rows with None task IDs
        none_task_ids = df_processed[df_processed['Task ID'].isna()]
        if not none_task_ids.empty:
            logger.log(f"Rows with None Task IDs:")
            for idx, row in none_task_ids.iterrows():
                logger.log(f"  SEQ {row[SEQ_NO_COLUMN]}: {row[TITLE_COLUMN]}")
            logger.log("")

        # Calculate total base hours
        total_base_mhrs = df_processed['Base Hours'].sum()

        # Calculate type coefficient breakdown (uses appropriate dataframe based on setting)
        type_coeff_breakdown = calculate_type_coefficient_breakdown(df_original_for_coeff, df_processed)
        type_coefficient_hours = calculate_total_type_coefficient_hours(df_original_for_coeff, df_processed)

        # Get the bonus hours amount for this aircraft/check combination
        bonus_hours = get_bonus_hours(ac_type, wp_type, bonus_lookup)

        # Get bonus breakdown by source (which sheets contributed)
        bonus_breakdown = get_bonus_breakdown_by_source(ac_type, wp_type)

        logger.log_header("BONUS BREAKDOWN")
        logger.log(f"Bonus from files: {bonus_breakdown}")
        logger.log(f"Type coeff breakdown: {type_coeff_breakdown}")
        logger.log("")

        # Combine bonus breakdown with type coefficient breakdown
        # Type coefficients are shown as bonus items
        combined_bonus_breakdown = {}

        # Add regular bonus hours
        if bonus_breakdown:
            for source, hours in bonus_breakdown.items():
                if hours > 0:
                    combined_bonus_breakdown[source] = hours

        # Add type coefficient as bonus items
        if type_coeff_breakdown:
            for special_type, additional_hours in type_coeff_breakdown.items():
                if abs(additional_hours) > 0.01:  # Only show non-zero values
                    combined_bonus_breakdown[f"Type Coefficient ({special_type})"] = additional_hours

        logger.log_header("COMBINED BREAKDOWN")
        logger.log(f"Combined: {combined_bonus_breakdown}")
        logger.log("")

        # Calculate total additional hours (bonus + type coefficient)
        total_additional_hours = bonus_hours + type_coefficient_hours

        logger.log_header("TOTALS BEFORE APPLYING BONUS")
        logger.log(f"Bonus hours: {bonus_hours:.2f}")
        logger.log(f"Type coefficient hours: {type_coefficient_hours:.2f}")
        logger.log(f"Total additional: {total_additional_hours:.2f}")
        logger.log("")

        # Apply bonus hours to dataframe (adds fixed bonus to adjusted hours)
        df_processed = apply_bonus_hours(df_processed, ac_type, wp_type, bonus_lookup)

        # Calculate total man-hours AFTER all adjustments
        total_mhrs = df_processed['Adjusted Hours'].sum()

        logger.log_header("FINAL TOTALS")
        logger.log(f"Total Base: {total_base_mhrs:.2f}")
        logger.log(f"Total Additional: {total_additional_hours:.2f}")
        logger.log(f"Total Man-Hours: {total_mhrs:.2f}")
        logger.log(f"Calculation check: {total_base_mhrs:.2f} + {total_additional_hours:.2f} = {total_base_mhrs + total_additional_hours:.2f}")
        logger.log("")

        # Identify high man-hours tasks (using adjusted hours AFTER bonus)
        high_mhrs_tasks = df_processed[df_processed['Adjusted Hours'] > HIGH_MHRS_HOURS]

        # Check for new task IDs (only for rows that should be checked)
        new_task_ids_with_seq = identify_new_task_ids(
            df_processed,
            reference_data['task_ids'],
            reference_data['eo_ids']
        )

        # Generate a random sample for debugging (only from processed rows)
        sample_size = min(RANDOM_SAMPLE_SIZE, len(df_processed))
        random_sample = df_processed.sample(n=sample_size, random_state=1) if len(df_processed) > 0 else pd.DataFrame()

        # Calculate special code distribution if enabled (using adjusted hours AFTER bonus)
        special_code_distribution = None
        special_code_per_day = None
        if enable_special_code_processing:
            special_code_distribution = calculate_special_code_distribution(df_processed)
            special_code_per_day = calculate_special_code_per_day(
                special_code_distribution,
                workpack_info['workpack_days']
            )

        logger.log_separator()
        logger.log("SUMMARY")
        logger.log_separator()
        logger.log(f"Total Base Man-Hours: {hours_to_hhmm(total_base_mhrs)}")
        logger.log(f"Type Coefficient Additional Hours: {hours_to_hhmm(type_coefficient_hours)}")
        if bonus_hours > 0:
            logger.log(f"Bonus Hours: +{hours_to_hhmm(bonus_hours)}")
        logger.log(f"Total Additional Hours: {hours_to_hhmm(total_additional_hours)}")
        logger.log(f"Final Total: {hours_to_hhmm(total_mhrs)}")
        logger.log_separator()
        logger.log("")

        # Return structured data dictionary
        return {
            'total_mhrs': total_mhrs,
            'total_base_mhrs': total_base_mhrs,
            'total_additional_hours': total_additional_hours,
            'bonus_breakdown': combined_bonus_breakdown,  # Combined bonus + type coefficient
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