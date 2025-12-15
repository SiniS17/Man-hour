"""
Type Coefficient Module
Handles type coefficient lookup and application based on special type column
"""

import pandas as pd
import os
from core.config import (REFERENCE_FOLDER, TYPE_COEFFICIENT_FILE,
                         TYPE_COEFF_AIRCRAFT_COLUMN, TYPE_COEFF_PRODUCT_COLUMN,
                         TYPE_COEFF_COLUMN, SPECIAL_TYPE_COLUMN)


def load_type_coefficient_lookup():
    """
    Load type coefficients from ALL sheets in the coefficient file.
    Similar structure to bonus hours lookup.

    Expected structure:
    - Multiple sheets in the file (sheet names can be anything)
    - Each sheet contains rows with:
      * TYPE_COEFF_AIRCRAFT_COLUMN (e.g., "AircraftCode") - the aircraft type
      * TYPE_COEFF_PRODUCT_COLUMN (e.g., "ProductCode") - the check/product type
      * TYPE_COEFF_COLUMN (e.g., "Coeff") - the coefficient value

    Returns:
        dict: Nested dictionary {wp_type: {ac_type: {special_type: coefficient}}}
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

        print(f"\nLoading type coefficients from {TYPE_COEFFICIENT_FILE}...")
        print(f"Found {len(excel_file.sheet_names)} sheets to process")
        print(
            f"Column mapping: Aircraft='{TYPE_COEFF_AIRCRAFT_COLUMN}', Product='{TYPE_COEFF_PRODUCT_COLUMN}', Coeff='{TYPE_COEFF_COLUMN}'")

        total_rows_processed = 0

        for sheet_name in excel_file.sheet_names:
            # Read the sheet
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            print(f"\n  Processing sheet '{sheet_name}'...")

            # Check for required columns
            missing_cols = []
            if TYPE_COEFF_AIRCRAFT_COLUMN not in df.columns:
                missing_cols.append(TYPE_COEFF_AIRCRAFT_COLUMN)
            if TYPE_COEFF_PRODUCT_COLUMN not in df.columns:
                missing_cols.append(TYPE_COEFF_PRODUCT_COLUMN)
            if TYPE_COEFF_COLUMN not in df.columns:
                missing_cols.append(TYPE_COEFF_COLUMN)

            if missing_cols:
                print(f"    WARNING: Missing columns: {missing_cols}")
                print(f"    Available columns: {list(df.columns)}")
                continue

            # Process each row in the sheet
            rows_in_sheet = 0

            for idx, row in df.iterrows():
                # Get aircraft code/type
                ac_type = str(row[TYPE_COEFF_AIRCRAFT_COLUMN]).strip()

                # Skip rows with empty/invalid aircraft codes
                if pd.isna(row[TYPE_COEFF_AIRCRAFT_COLUMN]) or ac_type.lower() in ['nan', '', 'none']:
                    continue

                # Get product code (wp_type)
                wp_type = str(row[TYPE_COEFF_PRODUCT_COLUMN]).strip()

                # Skip rows with empty/invalid product codes
                if pd.isna(row[TYPE_COEFF_PRODUCT_COLUMN]) or wp_type.lower() in ['nan', '', 'none']:
                    continue

                # Get coefficient value
                try:
                    coefficient = float(row[TYPE_COEFF_COLUMN])
                except (ValueError, TypeError):
                    print(f"    WARNING: Invalid coefficient value in row {idx}")
                    continue

                # Use sheet name as the special type identifier
                special_type = sheet_name

                # Initialize nested dict if needed
                if wp_type not in coeff_lookup:
                    coeff_lookup[wp_type] = {}
                if ac_type not in coeff_lookup[wp_type]:
                    coeff_lookup[wp_type][ac_type] = {}

                # Store the coefficient for this combination
                coeff_lookup[wp_type][ac_type][special_type] = coefficient
                rows_in_sheet += 1
                total_rows_processed += 1

            print(f"    Loaded {rows_in_sheet} rows from sheet '{sheet_name}'")

        # Print summary
        print(f"\n✓ Successfully loaded type coefficients:")
        print(f"  - Total rows processed: {total_rows_processed}")
        print(f"  - Product codes found: {len(coeff_lookup)}")
        for wp_type in sorted(coeff_lookup.keys()):
            print(f"    • {wp_type}: {len(coeff_lookup[wp_type])} aircraft types")

        return coeff_lookup

    except Exception as e:
        print(f"ERROR loading type coefficient file: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_type_coefficient(ac_type, wp_type, special_type, coeff_lookup):
    """
    Look up type coefficient for given ac_type, wp_type, and special_type.

    Args:
        ac_type: Aircraft type (e.g., "B787")
        wp_type: Check/product type (e.g., "A06")
        special_type: Special type from the input file
        coeff_lookup: Dictionary from load_type_coefficient_lookup()

    Returns:
        float: Coefficient (1.0 if not found)
    """
    # Default coefficient
    default_coeff = 1.0

    if not coeff_lookup:
        return default_coeff

    if ac_type is None or wp_type is None:
        return default_coeff

    if special_type is None or pd.isna(special_type) or str(special_type).strip() == '':
        return default_coeff

    special_type_str = str(special_type).strip()

    # Look up the coefficient
    if wp_type not in coeff_lookup:
        return default_coeff

    if ac_type not in coeff_lookup[wp_type]:
        return default_coeff

    if special_type_str not in coeff_lookup[wp_type][ac_type]:
        return default_coeff

    coefficient = coeff_lookup[wp_type][ac_type][special_type_str]
    return coefficient


def apply_type_coefficients(df, ac_type, wp_type, coeff_lookup):
    """
    Apply type coefficients to the DataFrame based on special type column.

    This function:
    1. Checks if special type column exists
    2. If it doesn't exist, uses coefficient of 1.0 for all rows
    3. If it exists, looks up the coefficient for each row's special type
    4. Multiplies Base Hours by the coefficient to get Adjusted Hours

    Args:
        df: DataFrame with 'Base Hours' column
        ac_type: Aircraft type
        wp_type: Check/product type
        coeff_lookup: Dictionary from load_type_coefficient_lookup()

    Returns:
        DataFrame: Updated DataFrame with 'Type Coefficient' and 'Adjusted Hours' columns
    """
    # Check if special type column exists
    has_special_type = SPECIAL_TYPE_COLUMN in df.columns

    if not has_special_type:
        print(f"Info: Column '{SPECIAL_TYPE_COLUMN}' not found in input file")
        print(f"      Using default coefficient of 1.0 for all rows")
        df['Type Coefficient'] = 1.0
        df['Adjusted Hours'] = df['Base Hours']
        return df

    print(f"Info: Column '{SPECIAL_TYPE_COLUMN}' found in input file")
    print(f"      Applying type coefficients based on ac_type='{ac_type}', wp_type='{wp_type}'")

    # Apply coefficient for each row based on its special type
    def get_row_coefficient(row):
        special_type = row.get(SPECIAL_TYPE_COLUMN)
        return get_type_coefficient(ac_type, wp_type, special_type, coeff_lookup)

    df['Type Coefficient'] = df.apply(get_row_coefficient, axis=1)
    df['Adjusted Hours'] = df['Base Hours'] * df['Type Coefficient']

    # Print summary of coefficients applied
    coeff_counts = df['Type Coefficient'].value_counts().sort_index()
    print(f"\nType Coefficient Summary:")
    for coeff, count in coeff_counts.items():
        print(f"  Coefficient {coeff}: {count} rows")

    return df


def get_type_coefficient_breakdown(df):
    """
    Get a breakdown of type coefficients by special type.

    Args:
        df: DataFrame with Type Coefficient and special type columns

    Returns:
        dict: {special_type: {'count': int, 'coefficient': float, 'total_hours': float}}
    """
    if SPECIAL_TYPE_COLUMN not in df.columns:
        return {}

    breakdown = {}

    for special_type in df[SPECIAL_TYPE_COLUMN].unique():
        if pd.isna(special_type):
            continue

        special_type_rows = df[df[SPECIAL_TYPE_COLUMN] == special_type]

        if len(special_type_rows) == 0:
            continue

        # Get the coefficient (should be same for all rows with this special type)
        coefficient = special_type_rows['Type Coefficient'].iloc[0]

        # Calculate additional hours from coefficient (difference from base)
        base_hours = special_type_rows['Base Hours'].sum()
        adjusted_hours = special_type_rows['Adjusted Hours'].sum()
        additional_hours = adjusted_hours - base_hours

        breakdown[str(special_type)] = {
            'count': len(special_type_rows),
            'coefficient': coefficient,
            'base_hours': base_hours,
            'adjusted_hours': adjusted_hours,
            'additional_hours': additional_hours
        }

    return breakdown


def calculate_total_type_coefficient_hours(df):
    """
    Calculate total additional hours from type coefficients.

    Args:
        df: DataFrame with Base Hours and Adjusted Hours columns

    Returns:
        float: Total additional hours from type coefficients
    """
    total_base = df['Base Hours'].sum()
    total_adjusted = df['Adjusted Hours'].sum()
    return total_adjusted - total_base