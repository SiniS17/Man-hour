"""
Type Coefficient Module
Handles type coefficient lookup and application based on special type column

NEW LOGIC:
1. Take first letter of wp_type (e.g., "A06" -> "A" -> "A-check")
2. Look up coefficient using: ac_type + check_type + special_type (from "Function" column)
3. Formula: Adjusted Hours = Base Hours × Coefficient
"""

import pandas as pd
import os
from core.config import (REFERENCE_FOLDER, TYPE_COEFFICIENT_FILE,
                         TYPE_COEFF_FUNCTION_COLUMN, TYPE_COEFF_COLUMN,
                         SPECIAL_TYPE_COLUMN, TYPE_COEFFICIENT_PER_SEQ,
                         SEQ_NO_COLUMN, get_check_type_from_wp_type)


def load_type_coefficient_lookup():
    """
    Load type coefficients from the coefficient file.

    Expected structure in Standard_Work_Coe.xlsx:
    - Each sheet can have multiple rows
    - Columns: AircraftCode, Function (special type), Coeff
    - Sheet names represent check types (e.g., "A-check", "C-check", "Y-check")

    Returns:
        dict: Nested dictionary {check_type: {ac_type: {function: coefficient}}}
    """
    coeff_file_path = os.path.join(REFERENCE_FOLDER, TYPE_COEFFICIENT_FILE)

    if not os.path.exists(coeff_file_path):
        print(f"Info: Type coefficient file not found at {coeff_file_path}")
        print(f"      No type coefficients will be applied (defaulting to 1.0)")
        return {}

    try:
        # Load all sheets from the Excel file
        excel_file = pd.ExcelFile(coeff_file_path, engine='openpyxl')

        coeff_lookup = {}

        print(f"\n{'='*80}")
        print(f"LOADING TYPE COEFFICIENTS from {TYPE_COEFFICIENT_FILE}")
        print(f"{'='*80}")
        print(f"Found {len(excel_file.sheet_names)} sheets to process")
        print(f"Column mapping: Function='{TYPE_COEFF_FUNCTION_COLUMN}', Coeff='{TYPE_COEFF_COLUMN}'")

        total_rows_processed = 0

        for sheet_name in excel_file.sheet_names:
            # Read the sheet
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            print(f"\n  Processing sheet '{sheet_name}'...")

            # The sheet name is the check type (e.g., "A-check", "C-check", "Y-check")
            check_type = sheet_name

            # Check for required columns
            missing_cols = []

            # We need to find the aircraft code column - it might be named differently
            # Common names: AircraftCode, Aircraft, Type, etc.
            aircraft_col = None
            for possible_col in ['AircraftCode', 'Aircraft', 'Type', 'AC']:
                if possible_col in df.columns:
                    aircraft_col = possible_col
                    break

            if not aircraft_col:
                print(f"    WARNING: Could not find aircraft code column")
                print(f"    Available columns: {list(df.columns)}")
                continue

            if TYPE_COEFF_FUNCTION_COLUMN not in df.columns:
                missing_cols.append(TYPE_COEFF_FUNCTION_COLUMN)
            if TYPE_COEFF_COLUMN not in df.columns:
                missing_cols.append(TYPE_COEFF_COLUMN)

            if missing_cols:
                print(f"    WARNING: Missing columns: {missing_cols}")
                print(f"    Available columns: {list(df.columns)}")
                continue

            print(f"    Using aircraft column: '{aircraft_col}'")

            # Process each row in the sheet
            rows_in_sheet = 0

            for idx, row in df.iterrows():
                # Get aircraft type
                ac_type = str(row[aircraft_col]).strip()

                # Skip rows with empty/invalid aircraft types
                if pd.isna(row[aircraft_col]) or ac_type.lower() in ['nan', '', 'none']:
                    continue

                # Get function (special type)
                function = str(row[TYPE_COEFF_FUNCTION_COLUMN]).strip()

                # Skip rows with empty/invalid functions
                if pd.isna(row[TYPE_COEFF_FUNCTION_COLUMN]) or function.lower() in ['nan', '', 'none']:
                    continue

                # Get coefficient value
                try:
                    coefficient = float(row[TYPE_COEFF_COLUMN])
                except (ValueError, TypeError):
                    print(f"    WARNING: Invalid coefficient value in row {idx}")
                    continue

                # Initialize nested dict if needed
                if check_type not in coeff_lookup:
                    coeff_lookup[check_type] = {}
                if ac_type not in coeff_lookup[check_type]:
                    coeff_lookup[check_type][ac_type] = {}

                # Store the coefficient: check_type -> ac_type -> function -> coefficient
                coeff_lookup[check_type][ac_type][function] = coefficient
                rows_in_sheet += 1
                total_rows_processed += 1

            print(f"    Loaded {rows_in_sheet} rows from sheet '{sheet_name}'")

        # Print summary
        print(f"\n{'='*80}")
        print(f"✓ Successfully loaded type coefficients:")
        print(f"  - Total rows processed: {total_rows_processed}")
        print(f"  - Check types found: {len(coeff_lookup)}")
        for check_type in sorted(coeff_lookup.keys()):
            ac_types = len(coeff_lookup[check_type])
            total_functions = sum(len(functions) for functions in coeff_lookup[check_type].values())
            print(f"    • {check_type}: {ac_types} aircraft types, {total_functions} functions")
        print(f"{'='*80}\n")

        return coeff_lookup

    except Exception as e:
        print(f"ERROR loading type coefficient file: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_type_coefficient(ac_type, check_type, special_type, coeff_lookup):
    """
    Look up type coefficient for given ac_type, check_type, and special_type (function).

    Args:
        ac_type: Aircraft type (e.g., "B787")
        check_type: Check type (e.g., "A-check", "C-check", "Y-check")
        special_type: Special type from input file (matches "Function" column)
        coeff_lookup: Dictionary from load_type_coefficient_lookup()

    Returns:
        float: Coefficient (1.0 if not found)
    """
    # Default coefficient
    default_coeff = 1.0

    if not coeff_lookup:
        return default_coeff

    if ac_type is None or check_type is None:
        return default_coeff

    if special_type is None or pd.isna(special_type) or str(special_type).strip() == '':
        return default_coeff

    special_type_str = str(special_type).strip()

    # Look up: check_type -> ac_type -> function
    if check_type not in coeff_lookup:
        return default_coeff

    if ac_type not in coeff_lookup[check_type]:
        return default_coeff

    if special_type_str not in coeff_lookup[check_type][ac_type]:
        return default_coeff

    coefficient = coeff_lookup[check_type][ac_type][special_type_str]
    return coefficient


def apply_type_coefficients(df, ac_type, wp_type, coeff_lookup):
    """
    Apply type coefficients to the DataFrame based on special type column.

    Process:
    1. Extract check type from wp_type (e.g., "A06" -> "A-check")
    2. For each row, look up coefficient using: ac_type + check_type + special_type
    3. Calculate: Adjusted Hours = Base Hours × Coefficient

    Args:
        df: DataFrame with 'Base Hours' column
        ac_type: Aircraft type (e.g., "B787")
        wp_type: Work package type (e.g., "A06")
        coeff_lookup: Dictionary from load_type_coefficient_lookup()

    Returns:
        DataFrame: Updated DataFrame with 'Type Coefficient' and 'Adjusted Hours' columns
    """
    # Get check type from wp_type (e.g., "A06" -> "A-check")
    check_type = get_check_type_from_wp_type(wp_type)

    # Check if special type column exists
    has_special_type = SPECIAL_TYPE_COLUMN in df.columns

    if not has_special_type:
        print(f"Info: Column '{SPECIAL_TYPE_COLUMN}' not found in input file")
        print(f"      Using default coefficient of 1.0 for all rows")
        df['Type Coefficient'] = 1.0
        df['Adjusted Hours'] = df['Base Hours'].copy()
        return df

    print(f"\n{'='*80}")
    print(f"TYPE COEFFICIENT APPLICATION")
    print(f"{'='*80}")
    print(f"Aircraft Type: '{ac_type}'")
    print(f"WP Type: '{wp_type}' -> Check Type: '{check_type}'")
    print(f"Special Type Column: '{SPECIAL_TYPE_COLUMN}'")
    print(f"Mode: {'Per SEQ (once per SEQ)' if TYPE_COEFFICIENT_PER_SEQ else 'Per Row (all rows)'}")

    if not check_type:
        print(f"WARNING: Could not determine check type from wp_type '{wp_type}'")
        print(f"         Using default coefficient of 1.0 for all rows")
        df['Type Coefficient'] = 1.0
        df['Adjusted Hours'] = df['Base Hours'].copy()
        return df

    # Apply coefficient for each row based on its special type
    def get_row_coefficient(row):
        special_type = row.get(SPECIAL_TYPE_COLUMN)
        return get_type_coefficient(ac_type, check_type, special_type, coeff_lookup)

    df['Type Coefficient'] = df.apply(get_row_coefficient, axis=1)
    df['Adjusted Hours'] = df['Base Hours'] * df['Type Coefficient']

    # Print summary of coefficients applied
    print(f"\nCoefficient Distribution:")
    coeff_counts = df['Type Coefficient'].value_counts().sort_index()
    for coeff, count in coeff_counts.items():
        print(f"  {coeff:.2f}: {count} rows")

    # Show sample of special types and their coefficients
    if SPECIAL_TYPE_COLUMN in df.columns:
        special_type_sample = df[[SPECIAL_TYPE_COLUMN, 'Type Coefficient']].drop_duplicates().head(10)
        print(f"\nSpecial Type -> Coefficient Mapping (first 10):")
        for idx, row in special_type_sample.iterrows():
            st = row[SPECIAL_TYPE_COLUMN]
            coeff = row['Type Coefficient']
            print(f"  '{st}' -> {coeff:.2f}")

    print(f"{'='*80}\n")

    return df


def calculate_type_coefficient_breakdown(df_original, df_processed):
    """
    Calculate type coefficient bonus breakdown by special type.

    This calculates: (Adjusted Hours - Base Hours) for each special type

    Args:
        df_original: Original DataFrame (before deduplication)
        df_processed: Processed DataFrame (after deduplication if per_seq=True)

    Returns:
        dict: {special_type: additional_hours}
    """
    print(f"\n{'='*80}")
    print(f"TYPE COEFFICIENT BREAKDOWN CALCULATION")
    print(f"{'='*80}")
    print(f"Mode: {'Per SEQ (deduplicated)' if TYPE_COEFFICIENT_PER_SEQ else 'Per Row (all rows)'}")
    print(f"Original rows: {len(df_original)}")
    print(f"Processed rows (after dedup): {len(df_processed)}")

    # Use the appropriate dataframe based on TYPE_COEFFICIENT_PER_SEQ setting
    if TYPE_COEFFICIENT_PER_SEQ:
        df_to_use = df_processed
        print(f"Using: Processed (deduplicated) data")
    else:
        df_to_use = df_original
        print(f"Using: Original (all rows) data")

    # Check if special type column exists
    if SPECIAL_TYPE_COLUMN not in df_to_use.columns:
        print("No special type column found - returning empty breakdown")
        print(f"{'='*80}\n")
        return {}

    breakdown = {}

    print(f"\nBreakdown by Special Type:")

    # Group by special type and calculate additional hours
    for special_type in df_to_use[SPECIAL_TYPE_COLUMN].unique():
        if pd.isna(special_type) or str(special_type).strip() == '':
            continue

        # Get all rows with this special type
        special_type_rows = df_to_use[df_to_use[SPECIAL_TYPE_COLUMN] == special_type]

        if len(special_type_rows) == 0:
            continue

        # Calculate additional hours: (Adjusted - Base)
        base_hours = special_type_rows['Base Hours'].sum()
        adjusted_hours = special_type_rows['Adjusted Hours'].sum()
        additional_hours = adjusted_hours - base_hours

        print(f"  '{special_type}':")
        print(f"    Rows: {len(special_type_rows)}")
        print(f"    Base: {base_hours:.2f}h, Adjusted: {adjusted_hours:.2f}h, Additional: {additional_hours:.2f}h")

        # Only add to breakdown if there's an actual difference
        if abs(additional_hours) > 0.01:  # Avoid floating point errors
            breakdown[str(special_type)] = additional_hours

    print(f"\nFinal Breakdown: {breakdown}")
    print(f"{'='*80}\n")
    return breakdown


def calculate_total_type_coefficient_hours(df_original, df_processed):
    """
    Calculate total additional hours from type coefficients.

    Args:
        df_original: Original DataFrame (before deduplication)
        df_processed: Processed DataFrame (after deduplication if per_seq=True)

    Returns:
        float: Total additional hours from type coefficients
    """
    # Use the appropriate dataframe based on TYPE_COEFFICIENT_PER_SEQ setting
    if TYPE_COEFFICIENT_PER_SEQ:
        df_to_use = df_processed
    else:
        df_to_use = df_original

    total_base = df_to_use['Base Hours'].sum()
    total_adjusted = df_to_use['Adjusted Hours'].sum()
    total_additional = total_adjusted - total_base

    print(f"\n{'='*80}")
    print(f"TOTAL TYPE COEFFICIENT HOURS")
    print(f"{'='*80}")
    print(f"Total Base Hours: {total_base:.2f}")
    print(f"Total Adjusted Hours: {total_adjusted:.2f}")
    print(f"Total Additional Hours: {total_additional:.2f}")
    print(f"{'='*80}\n")

    return total_additional