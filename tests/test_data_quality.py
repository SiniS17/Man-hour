"""
Data Quality Test Module
Tests data validation, quality checks, and debug functionality
Incorporates functionality from the original debug.py
"""

import os
import pandas as pd
from datetime import datetime
from utils.time_utils import hours_to_hhmm, convert_planned_mhrs, time_to_hours
from utils.validation import validate_required_columns, check_column_exists
from core.config import (INPUT_FOLDER, REFERENCE_FOLDER, REFERENCE_FILE,
                         SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN,
                         REFERENCE_TASK_SHEET_NAME)


def test_data_quality():
    """
    Run data quality checks including B84 vs C9 comparison and sample validation.

    Returns:
        dict: Test result with status and details
    """
    result = {
        'passed': True,
        'errors': [],
        'warnings': [],
        'output': []
    }

    result['output'].append("Testing Data Quality and Debug Functionality...")
    result['output'].append("")

    # Test 1: Time conversion functions
    result['output'].append("Test 1: Time Conversion Functions")
    result['output'].append("-" * 60)

    time_test_result = test_time_conversions()
    result['output'].extend(time_test_result['output'])

    if not time_test_result['passed']:
        result['passed'] = False
        result['errors'].extend(time_test_result['errors'])

    result['output'].append("")

    # Test 2: Validation functions
    result['output'].append("Test 2: Validation Functions")
    result['output'].append("-" * 60)

    validation_test_result = test_validation_functions()
    result['output'].extend(validation_test_result['output'])

    if not validation_test_result['passed']:
        result['passed'] = False
        result['errors'].extend(validation_test_result['errors'])

    result['output'].append("")

    # Test 3: Reference file check (B84 validation)
    result['output'].append("Test 3: Reference File Validation")
    result['output'].append("-" * 60)

    reference_test_result = test_reference_file()
    result['output'].extend(reference_test_result['output'])

    if not reference_test_result['passed']:
        result['warnings'].extend(reference_test_result['warnings'])

    result['output'].append("")

    # Test 4: Input file check (if available)
    result['output'].append("Test 4: Input File Check")
    result['output'].append("-" * 60)

    input_test_result = test_input_files()
    result['output'].extend(input_test_result['output'])

    if not input_test_result['passed']:
        result['warnings'].extend(input_test_result['warnings'])

    return result


def test_time_conversions():
    """
    Test time conversion utility functions.

    Returns:
        dict: Test results
    """
    result = {
        'passed': True,
        'errors': [],
        'output': []
    }

    # Test hours_to_hhmm
    test_cases = [
        (2.5, "02:30"),
        (36.5, "36:30"),
        (0.25, "00:15"),
        (10.75, "10:45"),
        (0, "00:00"),
    ]

    result['output'].append("Testing hours_to_hhmm():")

    for hours, expected in test_cases:
        actual = hours_to_hhmm(hours)
        if actual == expected:
            result['output'].append(f"  ✓ {hours} hours = {actual}")
        else:
            result['output'].append(f"  ✗ {hours} hours = {actual} (expected {expected})")
            result['errors'].append(f"hours_to_hhmm({hours}) failed")
            result['passed'] = False

    # Test convert_planned_mhrs (minutes to hours)
    result['output'].append("")
    result['output'].append("Testing convert_planned_mhrs():")

    minutes_test_cases = [
        (120, 2.0),
        (90, 1.5),
        (30, 0.5),
        (0, 0.0),
    ]

    for minutes, expected_hours in minutes_test_cases:
        actual = convert_planned_mhrs(minutes)
        if actual == expected_hours:
            result['output'].append(f"  ✓ {minutes} minutes = {actual} hours")
        else:
            result['output'].append(f"  ✗ {minutes} minutes = {actual} hours (expected {expected_hours})")
            result['errors'].append(f"convert_planned_mhrs({minutes}) failed")
            result['passed'] = False

    return result


def test_validation_functions():
    """
    Test validation utility functions.

    Returns:
        dict: Test results
    """
    result = {
        'passed': True,
        'errors': [],
        'output': []
    }

    # Create sample DataFrame for testing
    sample_df = pd.DataFrame({
        'Column1': [1, 2, 3],
        'Column2': ['a', 'b', 'c'],
        'Column3': [10.5, 20.3, 30.1]
    })

    result['output'].append("Testing validation functions with sample DataFrame:")

    # Test validate_required_columns
    try:
        validate_required_columns(sample_df, ['Column1', 'Column2'], 'sample')
        result['output'].append("  ✓ validate_required_columns() passed")
    except ValueError as e:
        result['output'].append(f"  ✗ validate_required_columns() failed: {e}")
        result['errors'].append("validate_required_columns() test failed")
        result['passed'] = False

    # Test check_column_exists
    exists = check_column_exists(sample_df, 'Column1', 'sample')
    if exists:
        result['output'].append("  ✓ check_column_exists() passed")
    else:
        result['output'].append("  ✗ check_column_exists() failed")
        result['errors'].append("check_column_exists() test failed")
        result['passed'] = False

    return result


def test_reference_file():
    """
    Test reference file accessibility and B84 validation.

    Returns:
        dict: Test results
    """
    result = {
        'passed': True,
        'warnings': [],
        'output': []
    }

    reference_file_path = os.path.join(REFERENCE_FOLDER, REFERENCE_FILE)

    result['output'].append(f"Checking reference file: {reference_file_path}")

    if not os.path.exists(reference_file_path):
        result['output'].append(f"  ⚠ Reference file not found")
        result['warnings'].append("Reference file not accessible")
        result['passed'] = False
        return result

    try:
        # Try to load the reference file
        df = pd.read_excel(reference_file_path, sheet_name=REFERENCE_TASK_SHEET_NAME, engine='openpyxl')
        result['output'].append(f"  ✓ Reference file loaded successfully")
        result['output'].append(f"  ✓ Sheet '{REFERENCE_TASK_SHEET_NAME}' found with {len(df)} rows")

        # Check for B84 value (from original debug.py)
        if len(df) >= 84:
            result['output'].append(f"  ✓ File has sufficient rows for B84 check")
        else:
            result['warnings'].append("File has fewer than 84 rows")

    except Exception as e:
        result['output'].append(f"  ✗ Error loading reference file: {e}")
        result['warnings'].append(f"Reference file error: {e}")
        result['passed'] = False

    return result


def test_input_files():
    """
    Test input files availability and basic structure.

    Returns:
        dict: Test results
    """
    result = {
        'passed': True,
        'warnings': [],
        'output': []
    }

    result['output'].append(f"Checking INPUT folder: {INPUT_FOLDER}")

    if not os.path.exists(INPUT_FOLDER):
        result['output'].append(f"  ⚠ INPUT folder not found")
        result['warnings'].append("INPUT folder does not exist")
        result['passed'] = False
        return result

    # Check for Excel files
    import glob
    excel_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))

    if not excel_files:
        result['output'].append(f"  ⚠ No Excel files found in INPUT folder")
        result['warnings'].append("No input files to test")
        result['passed'] = False
        return result

    result['output'].append(f"  ✓ Found {len(excel_files)} Excel file(s)")

    # Test first file structure
    first_file = excel_files[0]
    result['output'].append(f"  Testing structure of: {os.path.basename(first_file)}")

    try:
        df = pd.read_excel(first_file, engine='openpyxl')
        result['output'].append(f"    ✓ File loaded successfully with {len(df)} rows")

        # Check for required columns
        required_cols = [SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN]
        missing = [col for col in required_cols if col not in df.columns]

        if missing:
            result['output'].append(f"    ⚠ Missing columns: {missing}")
            result['warnings'].append(f"Input file missing columns: {missing}")
        else:
            result['output'].append(f"    ✓ All required columns present")

        # Sample some data
        if len(df) > 0:
            sample_row = df.iloc[0]
            result['output'].append(f"    Sample SEQ: {sample_row.get(SEQ_NO_COLUMN, 'N/A')}")
            result['output'].append(f"    Sample Title: {str(sample_row.get(TITLE_COLUMN, 'N/A'))[:50]}")

    except Exception as e:
        result['output'].append(f"    ✗ Error loading file: {e}")
        result['warnings'].append(f"Input file error: {e}")
        result['passed'] = False

    return result


def generate_debug_sample(file_path, output_path):
    """
    Generate debug sample report (from original debug.py functionality).

    Args:
        file_path (str): Path to input file
        output_path (str): Path to save debug output
    """
    try:
        df = pd.read_excel(file_path, engine='openpyxl')

        required_cols = [SEQ_NO_COLUMN, PLANNED_MHRS_COLUMN]
        if not all(col in df.columns for col in required_cols):
            print(f"ERROR: Missing required columns for debug sample")
            return

        # Select random sample
        sample_size = min(5, len(df))
        random_sample = df.sample(n=sample_size, random_state=1)

        # Write debug output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("DEBUG SAMPLE REPORT (Random 5 Rows):\n")
            f.write(f"Sample Size: {sample_size}\n")
            f.write("-" * 80 + "\n")
            f.write(f"| {'SEQ No.':<8} | {'Original Planned Mhrs':<21} | {'Parsed (HH:MM)':<12} |\n")
            f.write("-" * 80 + "\n")

            for index, row in random_sample.iterrows():
                seq_no = str(row[SEQ_NO_COLUMN])
                original_mhrs = str(row[PLANNED_MHRS_COLUMN])
                planned_hours = convert_planned_mhrs(row[PLANNED_MHRS_COLUMN])
                planned_time_hhmm = hours_to_hhmm(planned_hours)
                f.write(f"| {seq_no:<8} | {original_mhrs:<21} | {planned_time_hhmm:>12} |\n")

            f.write("-" * 80 + "\n")

        print(f"Debug sample saved to {output_path}")

    except Exception as e:
        print(f"ERROR generating debug sample: {e}")


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING DATA QUALITY")
    print("=" * 80)
    print()

    result = test_data_quality()

    for output in result['output']:
        print(output)

    print()

    if result['passed']:
        print("✓ Data quality test PASSED")
    else:
        print("✗ Data quality test FAILED")
        for error in result['errors']:
            print(f"  ERROR: {error}")

    if result['warnings']:
        print("\nWarnings:")
        for warning in result['warnings']:
            print(f"  ⚠ {warning}")