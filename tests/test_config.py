"""
Configuration Test Module
Tests configuration loading and validation
"""

from core.config import (INPUT_FOLDER, OUTPUT_FOLDER, REFERENCE_FILE, REFERENCE_FOLDER,
                         SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN,
                         ENABLE_SPECIAL_CODE, ENABLE_TOOL_CONTROL,
                         SEQ_MAPPINGS, SEQ_ID_MAPPINGS, SEQ_COEFFICIENTS,
                         HIGH_MHRS_HOURS, RANDOM_SAMPLE_SIZE,
                         get_seq_coefficient, print_config)


def test_config():
    """
    Test configuration loading and validation.

    Returns:
        dict: Test result with status and details
    """
    result = {
        'passed': True,
        'errors': [],
        'warnings': [],
        'output': []
    }

    result['output'].append("Testing Configuration Loading...")

    # Test 1: Check required paths are configured
    try:
        assert INPUT_FOLDER, "INPUT_FOLDER is not configured"
        assert OUTPUT_FOLDER, "OUTPUT_FOLDER is not configured"
        assert REFERENCE_FILE, "REFERENCE_FILE is not configured"
        assert REFERENCE_FOLDER, "REFERENCE_FOLDER is not configured"
        result['output'].append("✓ All paths are configured")
    except AssertionError as e:
        result['passed'] = False
        result['errors'].append(str(e))

    # Test 2: Check required columns are configured
    try:
        assert SEQ_NO_COLUMN, "SEQ_NO_COLUMN is not configured"
        assert TITLE_COLUMN, "TITLE_COLUMN is not configured"
        assert PLANNED_MHRS_COLUMN, "PLANNED_MHRS_COLUMN is not configured"
        result['output'].append("✓ All required columns are configured")
    except AssertionError as e:
        result['passed'] = False
        result['errors'].append(str(e))

    # Test 3: Check SEQ mappings exist
    try:
        assert len(SEQ_MAPPINGS) > 0, "SEQ_MAPPINGS is empty"
        result['output'].append(f"✓ SEQ Mappings configured: {len(SEQ_MAPPINGS)} mappings")
    except AssertionError as e:
        result['passed'] = False
        result['errors'].append(str(e))

    # Test 4: Check SEQ ID mappings exist
    try:
        assert len(SEQ_ID_MAPPINGS) > 0, "SEQ_ID_MAPPINGS is empty"
        result['output'].append(f"✓ SEQ ID Mappings configured: {len(SEQ_ID_MAPPINGS)} mappings")
    except AssertionError as e:
        result['passed'] = False
        result['errors'].append(str(e))

    # Test 5: Check coefficients if configured
    if len(SEQ_COEFFICIENTS) > 0:
        result['output'].append(f"✓ SEQ Coefficients configured: {len(SEQ_COEFFICIENTS)} coefficients")

        # Test coefficient function
        try:
            test_coeff = get_seq_coefficient("2.1")
            assert isinstance(test_coeff, float), "Coefficient should be float"
            result['output'].append(f"✓ Coefficient function works (SEQ 2.1 = {test_coeff})")
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Coefficient function error: {e}")
    else:
        result['warnings'].append("No SEQ coefficients configured (using default)")

    # Test 6: Check feature flags
    result['output'].append(f"✓ Special Code feature: {'Enabled' if ENABLE_SPECIAL_CODE else 'Disabled'}")
    result['output'].append(f"✓ Tool Control feature: {'Enabled' if ENABLE_TOOL_CONTROL else 'Disabled'}")

    # Test 7: Check thresholds
    try:
        assert HIGH_MHRS_HOURS > 0, "HIGH_MHRS_HOURS should be positive"
        assert RANDOM_SAMPLE_SIZE > 0, "RANDOM_SAMPLE_SIZE should be positive"
        result['output'].append(f"✓ Thresholds configured: High Mhrs={HIGH_MHRS_HOURS}, Sample={RANDOM_SAMPLE_SIZE}")
    except AssertionError as e:
        result['passed'] = False
        result['errors'].append(str(e))

    # Print config for verification
    result['output'].append("\nConfiguration Details:")
    result['output'].append("-" * 60)

    # Capture print_config output (it prints directly)
    print("\nCurrent Configuration:")
    print_config()

    return result


def validate_seq_mappings():
    """
    Validate SEQ mappings are properly configured.

    Returns:
        bool: True if valid, False otherwise
    """
    required_seqs = ["SEQ_2.X", "SEQ_3.X", "SEQ_4.X"]

    for seq in required_seqs:
        if seq not in SEQ_MAPPINGS:
            print(f"WARNING: {seq} not found in SEQ_MAPPINGS")
            return False

    return True


def validate_coefficients():
    """
    Validate that coefficients are numeric and reasonable.

    Returns:
        bool: True if valid, False otherwise
    """
    for key, value in SEQ_COEFFICIENTS.items():
        if not isinstance(value, (int, float)):
            print(f"ERROR: Coefficient for {key} is not numeric: {value}")
            return False

        if value < 0 or value > 10:
            print(f"WARNING: Coefficient for {key} seems unusual: {value}")

    return True


if __name__ == "__main__":
    result = test_config()

    if result['passed']:
        print("\n✓ Configuration test PASSED")
    else:
        print("\n✗ Configuration test FAILED")
        for error in result['errors']:
            print(f"  ERROR: {error}")