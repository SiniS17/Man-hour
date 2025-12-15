"""
Data Processor Module
Core processing logic for workpack data analysis
"""

import pandas as pd
from utils.time_utils import convert_planned_mhrs, hours_to_hhmm
from utils.validation import validate_required_columns
from core.config import (SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN,
                         HIGH_MHRS_HOURS, RANDOM_SAMPLE_SIZE,
                         ENABLE_SPECIAL_CODE, SPECIAL_CODE_COLUMN,
                         ENABLE_TOOL_CONTROL, REFERENCE_EO_PREFIX)
from core.id_extractor import extract_task_id
from core.data_loader import load_input_dataframe, extract_workpack_dates
from features.special_code import (calculate_special_code_distribution,
                                   calculate_special_code_per_day,
                                   validate_special_code_column)
from features.coefficients import apply_coefficients_to_dataframe, print_coefficient_summary
from features.a_extractor import (extract_from_dataframe, load_bonus_hours_lookup,
                                  apply_bonus_hours)

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
    # Load the uploaded file
    df = load_input_dataframe(input_file_path)

    # Extract workpack dates
    workpack_info = extract_workpack_dates(df)

    # Extract ac_type and wp_type from column A (first row only, since all rows are the same)
    ac_type, wp_type, ac_name = extract_from_dataframe(df)

    # Load bonus hours lookup table
    bonus_lookup = load_bonus_hours_lookup()

    # Build list of required columns based on configuration
    required_columns = [SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN]

    # Validate special code configuration
    enable_special_code_processing = False
    if ENABLE_SPECIAL_CODE:
        is_valid, error_msg = validate_special_code_column(df, SPECIAL_CODE_COLUMN)
        if not is_valid:
            print(f"WARNING: {error_msg}")
            print("Proceeding without special code analysis...")
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

    # Apply SEQ coefficient to get adjusted hours
    df = apply_coefficients_to_dataframe(df)

    # Apply bonus hours based on ac_type and wp_type
    df = apply_bonus_hours(df, ac_type, wp_type, bonus_lookup)

    # Extract task IDs and check flags
    task_id_data = df.apply(extract_task_id, axis=1)
    df['Task ID'] = task_id_data.apply(lambda x: x[0])
    df['Should Check Reference'] = task_id_data.apply(lambda x: x[1])
    df['Should Process'] = task_id_data.apply(lambda x: x[2])

    # Filter out rows that should not be processed (ignore mode)
    df_processed = df[df['Should Process'] == True].copy()

    # IMPORTANT: Keep only the FIRST occurrence of each SEQ to avoid duplicate man-hour counting
    df_processed = df_processed.drop_duplicates(subset=[SEQ_NO_COLUMN], keep='first')

    print(f"\nTotal rows: {len(df)}")
    print(f"Rows to process (after removing duplicates): {len(df_processed)}")
    print(f"Rows ignored: {len(df) - len(df_processed)}")

    # Show coefficient application summary
    print_coefficient_summary(df_processed)

    # Debugging: Print rows with None task IDs
    none_task_ids = df_processed[df_processed['Task ID'].isna()]
    if not none_task_ids.empty:
        print(f"Rows with None Task IDs (Seq. No. and respective rows):")
        print(none_task_ids[[SEQ_NO_COLUMN, TITLE_COLUMN, 'Task ID']])

    # Identify high man-hours tasks (only from processed rows, using adjusted hours)
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

    # Calculate special code distribution if enabled (only from processed rows, using adjusted hours)
    special_code_distribution = None
    special_code_per_day = None
    if enable_special_code_processing:
        special_code_distribution = calculate_special_code_distribution(df_processed)
        special_code_per_day = calculate_special_code_per_day(
            special_code_distribution,
            workpack_info['workpack_days']
        )

    # Calculate total man-hours using ADJUSTED hours (with coefficient applied + bonus hours)
    total_mhrs = df_processed['Adjusted Hours'].sum()
    total_base_mhrs = df_processed['Base Hours'].sum()

    print(f"\nTotal Base Man-Hours: {hours_to_hhmm(total_base_mhrs)}")
    print(f"Total Adjusted Man-Hours (with coefficients + bonus): {hours_to_hhmm(total_mhrs)}")

    # Return structured data dictionary
    return {
        'total_mhrs': total_mhrs,
        'total_base_mhrs': total_base_mhrs,
        'total_mhrs_hhmm': hours_to_hhmm(total_mhrs),
        'total_base_mhrs_hhmm': hours_to_hhmm(total_base_mhrs),
        'ac_type': ac_type,
        'ac_name': ac_name,  # ADD THIS LINE
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