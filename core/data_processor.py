"""
Data Processor Module
Core processing logic for workpack data analysis
UPDATED: Per-sheet SEQ filtering — MHR, New Task IDs, and Tool Control each use
         their own resolved SEQ mapping so rows can be included/excluded
         independently per output sheet.
UPDATED: New Task ID detection now carries the TITLE_COLUMN (Description) forward.
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
    should_process_for_sheet,
    SKIP_COEFFICIENT_CODES,
    ARRAY_SKIP_COEFFICIENT,
    # Per-sheet mappings
    SEQ_MHR_MAPPINGS,
    SEQ_NEWTASK_MAPPINGS,
    SEQ_TOOL_MAPPINGS,
    SEQ_MAPPINGS,
    SEQ_ID_MAPPINGS,
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
        df: DataFrame with 'Base Hours' and 'Task ID' columns

    Returns:
        DataFrame: Updated DataFrame with 'Coefficient' and 'Adjusted Hours' columns
    """
    logger = get_logger(module_name="data_processor")

    # Ensure a clean index before assigning new columns
    df = df.reset_index(drop=True)

    df['Coefficient'] = df.apply(
        lambda row: get_seq_coefficient(row[SEQ_NO_COLUMN], row.get('Task ID')),
        axis=1
    )
    df['Adjusted Hours'] = df['Base Hours'] * df['Coefficient']

    logger.info("SEQ COEFFICIENT APPLICATION")
    logger.info("-" * 80)
    logger.info("Coefficient Distribution:")
    coeff_counts = df['Coefficient'].value_counts().sort_index()
    for coeff, count in coeff_counts.items():
        logger.info(f"  {coeff:.2f}: {count} rows")

    if SKIP_COEFFICIENT_CODES:
        skip_count = len(df[df['Coefficient'] == ARRAY_SKIP_COEFFICIENT])
        if skip_count > 0:
            logger.info(f"  Skipped coefficient for {skip_count} rows (matched skip codes)")

    logger.info("")
    return df


def filter_df_for_sheet(df, sheet_mapping, label):
    """
    Filter a DataFrame to only include rows whose SEQ is not ignored
    according to the given per-sheet mapping.

    Args:
        df: DataFrame (must have SEQ_NO_COLUMN column)
        sheet_mapping: dict — one of SEQ_MHR_MAPPINGS / SEQ_NEWTASK_MAPPINGS / SEQ_TOOL_MAPPINGS
        label: human-readable label for logging

    Returns:
        pd.DataFrame: filtered copy with a clean integer index
    """
    logger = get_logger(module_name="data_processor")
    mask = df[SEQ_NO_COLUMN].apply(lambda s: should_process_for_sheet(s, sheet_mapping))
    filtered = df[mask].copy().reset_index(drop=True)
    excluded = len(df) - len(filtered)
    if excluded:
        logger.info(f"[{label}] Excluded {excluded} row(s) based on per-sheet SEQ mapping")
    return filtered


def process_data(input_file_path, reference_data):
    """
    Main data processing function.

    Args:
        input_file_path (str): Path to the input Excel file
        reference_data (dict): Dictionary containing 'task_ids' and 'eo_ids' sets

    Returns:
        dict: Dictionary with structured data for Excel output
    """
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    logger = get_logger(base_filename=base_filename)

    logger.info("="*80)
    logger.info("STARTING DATA PROCESSING")
    logger.info("="*80)
    logger.info(f"File: {input_file_path}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Load file
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

    # Validate special code configuration
    enable_special_code_processing = False
    if ENABLE_SPECIAL_CODE:
        is_valid, error_msg = validate_special_code_column(df, SPECIAL_CODE_COLUMN)
        if not is_valid:
            logger.warning(f"{error_msg}")
            logger.warning("Proceeding without special code analysis...")
        else:
            enable_special_code_processing = True

    # Check for required columns
    base_required = [SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN]
    validate_required_columns(df, base_required, input_file_path)

    # ── Tool Control (uses its own SEQ filter, operates on the raw full df) ──
    tool_control_issues = pd.DataFrame()
    if ENABLE_TOOL_CONTROL:
        # Build a mapping that the tool_control module can use for ID extraction
        # (it only needs SEQ_ID_MAPPINGS for task ID parsing, SEQ filter applied here)
        logger.info("TOOL CONTROL PROCESSING")
        logger.info("-"*80)
        logger.info(f"Effective SEQ mapping for Tool Control: {SEQ_TOOL_MAPPINGS}")
        tool_control_issues = process_tool_control(
            input_file_path,
            SEQ_TOOL_MAPPINGS,   # <-- per-sheet mapping passed to tool control
            SEQ_ID_MAPPINGS,
        )

    # Convert planned Mhrs (minutes) → hours
    df['Base Hours'] = df[PLANNED_MHRS_COLUMN].apply(convert_planned_mhrs)

    logger.info("AFTER BASE HOURS CALCULATION")
    logger.info("-"*80)
    logger.info(f"Total Base Hours (all rows): {df['Base Hours'].sum():.2f}")
    logger.info("")

    # Extract task IDs using the BASE mapping (used by both MHR and New Task paths)
    task_id_data = df.apply(extract_task_id, axis=1)
    df['Task ID'] = task_id_data.apply(lambda x: x[0])
    df['Should Check Reference'] = task_id_data.apply(lambda x: x[1])
    df['Should Process'] = task_id_data.apply(lambda x: x[2])

    # ── Rows that pass the base "Should Process" gate ──────────────────────
    df_base = df[df['Should Process'] == True].copy().reset_index(drop=True)

    # Deduplicate by SEQ (keep first occurrence); fall back to 'event' if that column exists
    dedup_col = 'event' if 'event' in df_base.columns else SEQ_NO_COLUMN
    df_base = df_base.drop_duplicates(subset=[dedup_col], keep='first').reset_index(drop=True)

    logger.info("AFTER DEDUPLICATION (base)")
    logger.info("-"*80)
    logger.info(f"Rows after base filter + dedup: {len(df_base)}")
    logger.info(f"Total Base Hours (base): {df_base['Base Hours'].sum():.2f}")
    logger.info("")

    # ════════════════════════════════════════════════════════════════════════
    # MAN-HOURS calculation — apply per-sheet SEQ filter
    # ════════════════════════════════════════════════════════════════════════
    logger.info("MHR SEQ FILTER")
    logger.info("-"*80)
    logger.info(f"Effective SEQ mapping for MHR: {SEQ_MHR_MAPPINGS}")
    df_mhr = filter_df_for_sheet(df_base, SEQ_MHR_MAPPINGS, "MHR")

    total_base_mhrs = df_mhr['Base Hours'].sum()

    # Identify high MHR tasks BEFORE coefficients (using base hours)
    high_mhrs_tasks = df_mhr[df_mhr['Base Hours'] > HIGH_MHRS_HOURS].copy()

    logger.info("HIGH MAN-HOURS TASKS DETECTION")
    logger.info("-"*80)
    logger.info(f"Threshold: {HIGH_MHRS_HOURS} hours")
    logger.info(f"Tasks exceeding threshold: {len(high_mhrs_tasks)}")
    logger.info("")

    # Apply SEQ-based coefficients (only on MHR subset)
    df_mhr = apply_seq_coefficients(df_mhr)

    logger.info("AFTER COEFFICIENT APPLICATION")
    logger.info("-"*80)
    logger.info(f"Total Base Hours: {df_mhr['Base Hours'].sum():.2f}")
    logger.info(f"Total Adjusted Hours: {df_mhr['Adjusted Hours'].sum():.2f}")
    logger.info(f"Coefficient Effect: {(df_mhr['Adjusted Hours'].sum() - df_mhr['Base Hours'].sum()):.2f}")
    logger.info("")

    # Bonus hours
    bonus_hours = get_bonus_hours(ac_type, wp_type, bonus_lookup)
    bonus_breakdown = get_bonus_breakdown_by_source(ac_type, wp_type, file_logger=logger)

    coefficient_effect = df_mhr['Adjusted Hours'].sum() - df_mhr['Base Hours'].sum()
    total_after_coefficient = df_mhr['Adjusted Hours'].sum()
    total_mhrs = total_after_coefficient + bonus_hours

    logger.info("TOTALS CALCULATION")
    logger.info("-"*80)
    logger.info(f"Base hours: {total_base_mhrs:.2f}")
    logger.info(f"Coefficient effect: +{coefficient_effect:.2f}")
    logger.info(f"Total after coefficient: {total_after_coefficient:.2f}")
    logger.info(f"Bonus hours: +{bonus_hours:.2f}")
    logger.info(f"Final total: {total_mhrs:.2f}")
    logger.info("")

    # ════════════════════════════════════════════════════════════════════════
    # NEW TASK IDs — apply per-sheet SEQ filter
    # ════════════════════════════════════════════════════════════════════════
    logger.info("NEW TASK ID SEQ FILTER")
    logger.info("-"*80)
    logger.info(f"Effective SEQ mapping for New Task IDs: {SEQ_NEWTASK_MAPPINGS}")

    # Re-extract task IDs for the New Task sheet using NEWTASK mapping.
    # We go back to df (full, pre-base-filter) so that SEQs ignored in the
    # base mapping but enabled in SEQ_NEWTASK_MAPPINGS can still appear.
    df['Base Hours'] = df[PLANNED_MHRS_COLUMN].apply(convert_planned_mhrs)  # already done, but safe
    task_id_data_full = df.apply(
        lambda row: _extract_task_id_with_mapping(row, SEQ_NEWTASK_MAPPINGS),
        axis=1
    )
    df['_NT_Task_ID'] = task_id_data_full.apply(lambda x: x[0])
    df['_NT_Should_Check'] = task_id_data_full.apply(lambda x: x[1])
    df['_NT_Should_Process'] = task_id_data_full.apply(lambda x: x[2])

    df_newtask = df[df['_NT_Should_Process'] == True].copy().reset_index(drop=True)
    dedup_col_nt = 'event' if 'event' in df_newtask.columns else SEQ_NO_COLUMN
    df_newtask = df_newtask.drop_duplicates(subset=[dedup_col_nt], keep='first').reset_index(drop=True)

    # Drop the original 'Task ID' / 'Should Check Reference' cols that were added
    # to df during the base-mapping pass — if we rename _NT_ cols to the same names,
    # pandas ends up with two identically-named columns which causes the
    # "cannot reindex on an axis with duplicate labels" error.
    cols_to_drop = [c for c in ['Task ID', 'Should Check Reference'] if c in df_newtask.columns]
    if cols_to_drop:
        df_newtask = df_newtask.drop(columns=cols_to_drop)

    # Rename helper cols for identify function
    df_newtask = df_newtask.rename(columns={
        '_NT_Task_ID': 'Task ID',
        '_NT_Should_Check': 'Should Check Reference',
    })

    new_task_ids_with_seq = identify_new_task_ids(
        df_newtask,
        reference_data['task_ids'],
        reference_data['eo_ids'],
    )

    # ── Random debug sample (from MHR set) ──────────────────────────────────
    sample_size = min(RANDOM_SAMPLE_SIZE, len(df_mhr))
    random_sample = df_mhr.sample(n=sample_size, random_state=1) if len(df_mhr) > 0 else pd.DataFrame()

    # Special code distribution (MHR set)
    special_code_distribution = None
    special_code_per_day = None
    if enable_special_code_processing:
        special_code_distribution = calculate_special_code_distribution(df_mhr)
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

    write_debug_sample_to_log(logger, random_sample, enable_special_code_processing)

    WorkpackLogger().close_file_logger(base_filename)

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
        'high_mhrs_threshold': HIGH_MHRS_HOURS,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_task_id_with_mapping(row, sheet_mapping):
    """
    Variant of extract_task_id that uses a per-sheet SEQ mapping to decide
    whether to process a row, instead of the base SEQ_MAPPINGS.

    Returns:
        tuple: (task_id, should_check_reference, should_process)
    """
    from core.id_extractor import extract_id_from_title
    from core.config import SEQ_ID_MAPPINGS

    seq_no = str(row[SEQ_NO_COLUMN])
    seq_prefix = seq_no.split('.')[0]
    mapping_key = f"SEQ_{seq_prefix}.X"

    seq_mapping_value = sheet_mapping.get(mapping_key, 'true')

    if seq_mapping_value == 'ignore':
        return (None, False, False)

    id_mapping_key = f"SEQ_{seq_prefix}.X_ID"
    id_extraction_method = SEQ_ID_MAPPINGS.get(id_mapping_key, '/')

    title = str(row[TITLE_COLUMN])
    task_id = extract_id_from_title(title, id_extraction_method)
    should_check = (seq_mapping_value == 'true')

    return (task_id, should_check, True)


def identify_new_task_ids(df_processed, reference_task_ids, reference_eo_ids):
    """
    Identify task IDs not present in the reference data.
    Carries the TITLE_COLUMN (Description) into the result.
    """
    rows_to_check = df_processed[df_processed['Should Check Reference'] == True].copy().reset_index(drop=True)
    rows_to_check['Is_EO'] = rows_to_check['Task ID'].astype(str).str.startswith(REFERENCE_EO_PREFIX)

    eo_rows = rows_to_check[rows_to_check['Is_EO'] == True].copy().reset_index(drop=True)
    new_eo_rows = eo_rows[~eo_rows['Task ID'].isin(reference_eo_ids)].copy().reset_index(drop=True)

    task_rows = rows_to_check[rows_to_check['Is_EO'] == False].copy().reset_index(drop=True)
    new_task_rows = task_rows[~task_rows['Task ID'].isin(reference_task_ids)].copy().reset_index(drop=True)

    cols = [SEQ_NO_COLUMN, 'Task ID', TITLE_COLUMN]
    # Guard: only select columns that actually exist
    cols = [c for c in cols if c in df_processed.columns]

    new_task_ids_with_seq = pd.concat([new_eo_rows, new_task_rows]).reset_index(drop=True)[cols].copy()
    return new_task_ids_with_seq


def write_debug_sample_to_log(logger, debug_df, enable_special_code):
    """Write the debug sample section to the log file."""
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