"""
Type Coefficient Module
Handles type coefficient lookup and application based on special type column

LOGIC:
1. Load coefficient file (single sheet, sheet name is irrelevant)
2. Filter by IsActive = TRUE
3. Look up using: AircraftCode + CheckGroup + FuncGroup
4. Formula: Adjusted Hours = Base Hours × Coeff
"""

import pandas as pd
import os
from core.config import (REFERENCE_FOLDER, TYPE_COEFFICIENT_FILE,
                         TYPE_COEFF_AIRCRAFT_COLUMN, TYPE_COEFF_CHECKGROUP_COLUMN,
                         TYPE_COEFF_FUNCTION_COLUMN, TYPE_COEFF_COLUMN,
                         TYPE_COEFF_ISACTIVE_COLUMN,
                         SPECIAL_TYPE_COLUMN, TYPE_COEFFICIENT_PER_SEQ,
                         SEQ_NO_COLUMN, get_check_type_from_wp_type)

# Global logger instance (will be set by data_processor)
_logger = None


def set_logger(logger):
    """Set the logger instance for this module"""
    global _logger
    _logger = logger


def log(message, to_console=True):
    """Write to log and optionally console"""
    if _logger:
        _logger.log(message, to_console)
    else:
        if to_console:
            print(message)


def load_type_coefficient_lookup():
    """
    Load type coefficients from the coefficient file.

    Structure:
    - Single file with one or more sheets (sheet names are irrelevant)
    - Required columns: AircraftCode, CheckGroup, FuncGroup, Coeff
    - Optional column: IsActive (if present, only load rows where IsActive = TRUE)

    Lookup key: CheckGroup -> AircraftCode -> FuncGroup -> Coeff

    Returns:
        dict: Nested dictionary {check_group: {aircraft_code: {func_group: coeff}}}
    """
    coeff_file_path = os.path.join(REFERENCE_FOLDER, TYPE_COEFFICIENT_FILE)

    if not os.path.exists(coeff_file_path):
        log(f"Info: Type coefficient file not found at {coeff_file_path}")
        log(f"      No type coefficients will be applied (defaulting to 1.0)")
        return {}

    try:
        # Load all sheets from the Excel file
        excel_file = pd.ExcelFile(coeff_file_path, engine='openpyxl')

        coeff_lookup = {}

        log("")
        log("="*80)
        log(f"LOADING TYPE COEFFICIENTS from {TYPE_COEFFICIENT_FILE}")
        log("="*80)
        log(f"Found {len(excel_file.sheet_names)} sheet(s) - will process all (sheet names irrelevant)")
        log(f"Required columns: {TYPE_COEFF_AIRCRAFT_COLUMN}, {TYPE_COEFF_CHECKGROUP_COLUMN}, {TYPE_COEFF_FUNCTION_COLUMN}, {TYPE_COEFF_COLUMN}")
        if TYPE_COEFF_ISACTIVE_COLUMN:
            log(f"Filter column: {TYPE_COEFF_ISACTIVE_COLUMN} (only TRUE)")

        total_rows_processed = 0
        total_rows_skipped_inactive = 0

        # Process ALL sheets (combine them)
        all_data = []
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            log(f"\n  Reading sheet '{sheet_name}': {len(df)} rows")
            all_data.append(df)

        # Combine all sheets into one dataframe
        df_combined = pd.concat(all_data, ignore_index=True)
        log(f"\nCombined total: {len(df_combined)} rows from all sheets")

        # Check for required columns
        required_cols = [TYPE_COEFF_AIRCRAFT_COLUMN, TYPE_COEFF_CHECKGROUP_COLUMN,
                        TYPE_COEFF_FUNCTION_COLUMN, TYPE_COEFF_COLUMN]
        missing_cols = [col for col in required_cols if col not in df_combined.columns]

        if missing_cols:
            log(f"ERROR: Missing required columns: {missing_cols}")
            log(f"Available columns: {list(df_combined.columns)}")
            return {}

        # Filter by IsActive = TRUE if column exists
        if TYPE_COEFF_ISACTIVE_COLUMN and TYPE_COEFF_ISACTIVE_COLUMN in df_combined.columns:
            rows_before = len(df_combined)
            df_combined = df_combined[df_combined[TYPE_COEFF_ISACTIVE_COLUMN] == True].copy()
            total_rows_skipped_inactive = rows_before - len(df_combined)
            log(f"\nFiltered by {TYPE_COEFF_ISACTIVE_COLUMN} = TRUE:")
            log(f"  Active rows: {len(df_combined)}")
            log(f"  Skipped (inactive): {total_rows_skipped_inactive}")

        log(f"\nProcessing {len(df_combined)} active rows...")

        # Process each row
        for idx, row in df_combined.iterrows():
            # Get aircraft code
            aircraft_code = str(row[TYPE_COEFF_AIRCRAFT_COLUMN]).strip()
            if pd.isna(row[TYPE_COEFF_AIRCRAFT_COLUMN]) or aircraft_code.lower() in ['nan', '', 'none']:
                continue

            # Get check group
            check_group = str(row[TYPE_COEFF_CHECKGROUP_COLUMN]).strip()
            if pd.isna(row[TYPE_COEFF_CHECKGROUP_COLUMN]) or check_group.lower() in ['nan', '', 'none']:
                continue

            # Get function group
            func_group = str(row[TYPE_COEFF_FUNCTION_COLUMN]).strip()
            if pd.isna(row[TYPE_COEFF_FUNCTION_COLUMN]) or func_group.lower() in ['nan', '', 'none']:
                continue

            # Get coefficient
            try:
                coeff = float(row[TYPE_COEFF_COLUMN])
            except (ValueError, TypeError):
                log(f"  WARNING: Invalid coefficient value at row {idx}")
                continue

            # Store: check_group -> aircraft_code -> func_group -> coeff
            if check_group not in coeff_lookup:
                coeff_lookup[check_group] = {}
            if aircraft_code not in coeff_lookup[check_group]:
                coeff_lookup[check_group][aircraft_code] = {}

            coeff_lookup[check_group][aircraft_code][func_group] = coeff
            total_rows_processed += 1

        # Print summary
        log("")
        log("="*80)
        log(f"✓ Successfully loaded type coefficients:")
        log(f"  - Total rows processed: {total_rows_processed}")
        if total_rows_skipped_inactive > 0:
            log(f"  - Rows skipped (inactive): {total_rows_skipped_inactive}")
        log(f"  - Check groups found: {len(coeff_lookup)}")

        for check_group in sorted(coeff_lookup.keys()):
            aircraft_count = len(coeff_lookup[check_group])
            func_count = sum(len(funcs) for funcs in coeff_lookup[check_group].values())
            log(f"    • {check_group}: {aircraft_count} aircraft, {func_count} functions")
        log("="*80)
        log("")

        return coeff_lookup

    except Exception as e:
        log(f"ERROR loading type coefficient file: {e}")
        import traceback
        log(traceback.format_exc())
        return {}


def get_type_coefficient(aircraft_code, check_group, func_group, coeff_lookup):
    """
    Look up type coefficient.

    Args:
        aircraft_code: Aircraft code (e.g., "B787")
        check_group: Check group (e.g., "A-CHECK")
        func_group: Function group from input file (e.g., "DIS", "LUB")
        coeff_lookup: Dictionary from load_type_coefficient_lookup()

    Returns:
        float: Coefficient (1.0 if not found)
    """
    default_coeff = 1.0

    if not coeff_lookup:
        return default_coeff

    if not aircraft_code or not check_group or not func_group:
        return default_coeff

    aircraft_code = str(aircraft_code).strip()
    check_group = str(check_group).strip()
    func_group = str(func_group).strip()

    # Lookup: check_group -> aircraft_code -> func_group
    if check_group not in coeff_lookup:
        return default_coeff

    if aircraft_code not in coeff_lookup[check_group]:
        return default_coeff

    if func_group not in coeff_lookup[check_group][aircraft_code]:
        return default_coeff

    return coeff_lookup[check_group][aircraft_code][func_group]


def apply_type_coefficients(df, ac_type, wp_type, coeff_lookup):
    """
    Apply type coefficients to the DataFrame.

    Process:
    1. Get check_group from wp_type (e.g., "A06" -> "A-CHECK")
    2. For each row, lookup coefficient using: ac_type + check_group + special_type
    3. Calculate: Adjusted Hours = Base Hours × Coefficient

    Args:
        df: DataFrame with 'Base Hours' column
        ac_type: Aircraft type (e.g., "B787")
        wp_type: Work package type (e.g., "A06")
        coeff_lookup: Dictionary from load_type_coefficient_lookup()

    Returns:
        DataFrame: Updated DataFrame with 'Type Coefficient' and 'Adjusted Hours' columns
    """
    # Get check group from wp_type
    check_group = get_check_type_from_wp_type(wp_type)

    # Check if special type column exists
    has_special_type = SPECIAL_TYPE_COLUMN in df.columns

    if not has_special_type:
        log(f"Info: Column '{SPECIAL_TYPE_COLUMN}' not found in input file")
        log(f"      Using default coefficient of 1.0 for all rows")
        df['Type Coefficient'] = 1.0
        df['Adjusted Hours'] = df['Base Hours'].copy()
        return df

    log("")
    log("="*80)
    log("TYPE COEFFICIENT APPLICATION")
    log("="*80)
    log(f"Aircraft Code: '{ac_type}'")
    log(f"WP Type: '{wp_type}' -> Check Group: '{check_group}'")
    log(f"Function Column: '{SPECIAL_TYPE_COLUMN}'")
    log(f"Mode: {'Per SEQ (once per SEQ)' if TYPE_COEFFICIENT_PER_SEQ else 'Per Row (all rows)'}")

    if not check_group:
        log(f"WARNING: Could not determine check group from wp_type '{wp_type}'")
        log(f"         Using default coefficient of 1.0 for all rows")
        df['Type Coefficient'] = 1.0
        df['Adjusted Hours'] = df['Base Hours'].copy()
        return df

    # Apply coefficient for each row
    def get_row_coefficient(row):
        func_group = row.get(SPECIAL_TYPE_COLUMN)
        coeff = get_type_coefficient(ac_type, check_group, func_group, coeff_lookup)
        return coeff

    df['Type Coefficient'] = df.apply(get_row_coefficient, axis=1)
    df['Adjusted Hours'] = df['Base Hours'] * df['Type Coefficient']

    # Print summary
    log(f"\nCoefficient Distribution:")
    coeff_counts = df['Type Coefficient'].value_counts().sort_index()
    for coeff, count in coeff_counts.items():
        log(f"  {coeff:.2f}: {count} rows")

    # Show sample mappings
    if SPECIAL_TYPE_COLUMN in df.columns:
        sample = df[[SPECIAL_TYPE_COLUMN, 'Type Coefficient']].drop_duplicates().head(15)
        log(f"\nFunction -> Coefficient Mapping (first 15):")
        for idx, row in sample.iterrows():
            func = row[SPECIAL_TYPE_COLUMN]
            coeff = row['Type Coefficient']
            log(f"  '{func}' -> {coeff:.2f}")

    log("="*80)
    log("")

    return df


def calculate_type_coefficient_breakdown(df_original, df_processed):
    """
    Calculate type coefficient breakdown by function group.

    Args:
        df_original: Original DataFrame (before deduplication)
        df_processed: Processed DataFrame (after deduplication if per_seq=True)

    Returns:
        dict: {func_group: additional_hours}
    """
    log("")
    log("="*80)
    log("TYPE COEFFICIENT BREAKDOWN")
    log("="*80)
    log(f"Mode: {'Per SEQ (deduplicated)' if TYPE_COEFFICIENT_PER_SEQ else 'Per Row (all rows)'}")

    df_to_use = df_processed if TYPE_COEFFICIENT_PER_SEQ else df_original

    log(f"Using: {len(df_to_use)} rows")

    if SPECIAL_TYPE_COLUMN not in df_to_use.columns:
        log("No function column found")
        log("="*80)
        return {}

    breakdown = {}
    total_base = 0
    total_adjusted = 0

    log(f"\nBy Function Group:")

    for func_group in df_to_use[SPECIAL_TYPE_COLUMN].unique():
        if pd.isna(func_group) or str(func_group).strip() == '':
            continue

        rows = df_to_use[df_to_use[SPECIAL_TYPE_COLUMN] == func_group]
        base = rows['Base Hours'].sum()
        adjusted = rows['Adjusted Hours'].sum()
        additional = adjusted - base

        total_base += base
        total_adjusted += adjusted

        log(f"  '{func_group}': {len(rows)} rows, Base={base:.2f}h, Adjusted={adjusted:.2f}h, Additional={additional:.2f}h")

        if abs(additional) > 0.01:
            breakdown[str(func_group)] = additional

    log(f"\n--- TOTALS ---")
    log(f"Total Base: {total_base:.2f}h")
    log(f"Total Adjusted: {total_adjusted:.2f}h")
    log(f"Total Additional: {(total_adjusted - total_base):.2f}h")
    log(f"Sum of breakdown: {sum(breakdown.values()):.2f}h")
    log("="*80)
    log("")

    return breakdown


def calculate_total_type_coefficient_hours(df_original, df_processed):
    """
    Calculate total additional hours from type coefficients.

    Args:
        df_original: Original DataFrame
        df_processed: Processed DataFrame

    Returns:
        float: Total additional hours
    """
    df_to_use = df_processed if TYPE_COEFFICIENT_PER_SEQ else df_original

    total_base = df_to_use['Base Hours'].sum()
    total_adjusted = df_to_use['Adjusted Hours'].sum()
    return total_adjusted - total_base