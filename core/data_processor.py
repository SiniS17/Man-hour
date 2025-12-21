"""
Data Processor Module
Core processing logic for workpack data analysis
UPDATED: Removed type coefficient, added SEQ coefficient system
"""

import os
from datetime import datetime

import pandas as pd

from core.config import (
    ENABLE_SPECIAL_CODE,
    ENABLE_TOOL_CONTROL,
    HIGH_MHRS_HOURS,
    PLANNED_MHRS_COLUMN,
    RANDOM_SAMPLE_SIZE,
    REFERENCE_EO_PREFIX,
    SEQ_NO_COLUMN,
    SPECIAL_CODE_COLUMN,
    TITLE_COLUMN,
    get_seq_coefficient,
)
from core.data_loader import extract_workpack_dates, load_input_dataframe
from core.id_extractor import extract_task_id
from features.a_extractor import (
    extract_from_dataframe,
    get_bonus_breakdown_by_source,
    get_bonus_hours,
    load_bonus_hours_lookup,
)
from features.special_code import (
    calculate_special_code_distribution,
    calculate_special_code_per_day,
    validate_special_code_column,
)
from utils.logger import WorkpackLogger, get_logger
from utils.time_utils import convert_planned_mhrs, hours_to_hhmm
from utils.validation import validate_required_columns

# Import tool control module if enabled
if ENABLE_TOOL_CONTROL:
    from features.tool_control import process_tool_control


def apply_seq_coefficients(df):
    """
    Apply SEQ-based coefficients to base hours.

    Args:
        df: DataFrame with 'Base Hours' column

    Returns:
        DataFrame: Updated DataFrame with 'Coefficient' and 'Adjusted Hours' columns
    """
    logger = get_logger(module_name="data_processor")

    # Apply coefficient based on SEQ number
    df['Coefficient'] = df[SEQ_NO_COLUMN].apply(get_seq_coefficient)

    # Calculate adjusted hours
    df['Adjusted Hours'] = df['Base Hours'] * df['Coefficient']

    logger.info("SEQ COEFFICIENT APPLICATION")
    logger.info("-"*80)
    logger.info("Coefficient Distribution:")
    coeff_counts = df['Coefficient'].value_counts().sort_index()
    for coeff, count in coeff_counts.items():
        logger.info(f"  {coeff:.2f}: {count} rows")
    logger.info("")

    return df


def process_data(input_file_path, reference_data):
    """
    Main data processing function.

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

    # Load bonus lookup
    bonus_lookup = load_bonus_hours_lookup()

    # Build list of required columns
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

    # Check tool availability if enabled
    tool_control_issues = pd.DataFrame()
    if ENABLE_TOOL_CONTROL:
        from core.config import SEQ_ID_MAPPINGS, SEQ_MAPPINGS
        tool_control_issues = process_tool_control(input_file_path, SEQ_MAPPINGS, SEQ_ID_MAPPINGS)

    # Convert "Planned Mhrs" (in minutes) to base hours
    df['Base Hours'] = df[PLANNED_MHRS_COLUMN].apply(convert_planned_mhrs)

    logger.info("AFTER BASE HOURS CALCULATION")
    logger.info("-"*80)
    logger.info(f"Total Base Hours (all rows): {df['Base Hours'].sum():.2f}")
    logger.info("")

    # Extract task IDs and check flags
    task_id_data = df.apply(extract_task_id, axis=1)
    df['Task ID'] = task_id_data.apply(lambda x: x[0])
    df['Should Check Reference'] = task_id_data.apply(lambda x: x[1])
    df['Should Process'] = task_id_data.apply(lambda x: x[2])

    # Filter out rows that should not be processed
    df_processed = df[df['Should Process'] == True].copy()

    # Deduplicate by SEQ (keep first occurrence)
    df_processed = df_processed.drop_duplicates(subset=[SEQ_NO_COLUMN], keep='first')

    logger.info("AFTER DEDUPLICATION")
    logger.info("-"*80)
    logger.info(f"Rows to process: {len(df_processed)}")
    logger.info(f"Total Base Hours (deduplicated): {df_processed['Base Hours'].sum():.2f}")
    logger.info("")

    # Calculate total base hours (BEFORE coefficients)
    total_base_mhrs = df_processed['Base Hours'].sum()

    # Apply SEQ-based coefficients
    df_processed = apply_seq_coefficients(df_processed)

    logger.info("AFTER COEFFICIENT APPLICATION")
    logger.info("-"*80)
    logger.info(f"Total Base Hours: {df_processed['Base Hours'].sum():.2f}")
    logger.info(f"Total Adjusted Hours: {df_processed['Adjusted Hours'].sum():.2f}")
    logger.info(f"Coefficient Effect: {(df_processed['Adjusted Hours'].sum() - df_processed['Base Hours'].sum()):.2f}")
    logger.info("")

    # Get the bonus hours (workpack-level, added once)
    bonus_hours = get_bonus_hours(ac_type, wp_type, bonus_lookup)

    # Get detailed bonus breakdown by source (this will log all details)
    bonus_breakdown = get_bonus_breakdown_by_source(ac_type, wp_type, file_logger=logger)

    # Calculate coefficient effect
    coefficient_effect = df_processed['Adjusted Hours'].sum() - df_processed['Base Hours'].sum()

    # Calculate total: Base + Coefficient Effect + Bonus
    total_after_coefficient = df_processed['Adjusted Hours'].sum()
    total_mhrs = total_after_coefficient + bonus_hours

    logger.info("TOTALS CALCULATION")
    logger.info("-"*80)
    logger.info(f"Base hours: {total_base_mhrs:.2f}")
    logger.info(f"Coefficient effect: +{coefficient_effect:.2f}")
    logger.info(f"Total after coefficient: {total_after_coefficient:.2f}")
    logger.info(f"Bonus hours: +{bonus_hours:.2f}")
    logger.info(f"Final total: {total_mhrs:.2f}")
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
    logger.info(f"Coefficient Effect: {hours_to_hhmm(coefficient_effect)}")
    logger.info(f"Bonus Hours: +{hours_to_hhmm(bonus_hours)}")
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
        'coefficient_effect': coefficient_effect,
        'bonus_hours': bonus_hours,
        'bonus_breakdown': bonus_breakdown,
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
    """
    rows_to_check = df_processed[df_processed['Should Check Reference'] == True].copy()
    rows_to_check['Is_EO'] = rows_to_check['Task ID'].astype(str).str.startswith(REFERENCE_EO_PREFIX)

    eo_rows = rows_to_check[rows_to_check['Is_EO'] == True]
    new_eo_rows = eo_rows[~eo_rows['Task ID'].isin(reference_eo_ids)]

    task_rows = rows_to_check[rows_to_check['Is_EO'] == False]
    new_task_rows = task_rows[~task_rows['Task ID'].isin(reference_task_ids)]

    new_task_ids_with_seq = pd.concat([new_eo_rows, new_task_rows])[[SEQ_NO_COLUMN, 'Task ID']].copy()

    return new_task_ids_with_seq


def write_debug_sample_to_log(logger, debug_df, enable_special_code):
    """
    Write the debug sample section to the log file.
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
        logger.info(f"| {SEQ_NO_COLUMN:<8} | Special Code | Task ID          | Coefficient | Base Mhrs | Adjusted Mhrs |")
        logger.info("-"*120)

        for idx, row in debug_df.iterrows():
            seq_no = str(row[SEQ_NO_COLUMN])
            special_code = str(row.get(SPECIAL_CODE_COLUMN, 'N/A')) if pd.notna(row.get(SPECIAL_CODE_COLUMN)) else "N/A"
            special_code = special_code[:12]
            task_id = str(row['Task ID'])[:16]
            coefficient = row.get('Coefficient', 1.0)
            base_hours = row.get('Base Hours', 0)
            adjusted_hours = row.get('Adjusted Hours', 0)
            base_time_hhmm = hours_to_hhmm(base_hours)
            adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

            logger.info(
                f"| {seq_no:<8} | {special_code:<12} | {task_id:<16} | {coefficient:<11.2f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |")
    else:
        logger.info(
            f"| {SEQ_NO_COLUMN:<8} | {TITLE_COLUMN[:30]:<30} | Task ID          | Coefficient | Base Mhrs | Adjusted Mhrs |")
        logger.info("-"*125)

        for idx, row in debug_df.iterrows():
            seq_no = str(row[SEQ_NO_COLUMN])
            title = str(row[TITLE_COLUMN])[:30]
            task_id = str(row['Task ID'])[:16]
            coefficient = row.get('Coefficient', 1.0)
            base_hours = row.get('Base Hours', 0)
            adjusted_hours = row.get('Adjusted Hours', 0)
            base_time_hhmm = hours_to_hhmm(base_hours)
            adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

            logger.info(
                f"| {seq_no:<8} | {title:<30} | {task_id:<16} | {coefficient:<11.2f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |")

    logger.info("-"*120)