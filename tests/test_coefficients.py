"""
Coefficient Test Module
Tests SEQ coefficient functionality and man-hour calculations
"""

from core.config import get_seq_coefficient, SEQ_COEFFICIENTS, DEFAULT_COEFFICIENT


def test_coefficients():
    """
    Test the coefficient retrieval and calculation functionality.

    Returns:
        dict: Test result with status and details
    """
    result = {
        'passed': True,
        'errors': [],
        'warnings': [],
        'output': []
    }

    result['output'].append("Testing SEQ Coefficient Functionality...")
    result['output'].append("")

    # Test cases: (seq_no, expected_coefficient, description)
    test_cases = [
        ("2.1", 2.0, "SEQ 2.x should have coefficient 2.0"),
        ("2.5", 2.0, "SEQ 2.x should have coefficient 2.0"),
        ("2.39", 2.0, "SEQ 2.x should have coefficient 2.0"),
        ("3.1", 2.0, "SEQ 3.x should have coefficient 2.0"),
        ("3.22", 2.0, "SEQ 3.x should have coefficient 2.0"),
        ("3.456", 2.0, "SEQ 3.x should have coefficient 2.0"),
        ("4.1", 1.0, "SEQ 4.x should have coefficient 1.0"),
        ("4.78", 1.0, "SEQ 4.x should have coefficient 1.0"),
        ("1.1", 1.0, "SEQ 1.x should have default coefficient 1.0"),
        ("5.1", 1.0, "SEQ 5.x should have default coefficient 1.0"),
        ("10.5", 1.0, "SEQ 10.x should have default coefficient 1.0"),
    ]

    result['output'].append("Test Cases:")
    result['output'].append("-" * 80)
    result['output'].append(f"{'SEQ No.':<12} {'Expected':<12} {'Actual':<12} {'Status':<12} {'Description':<30}")
    result['output'].append("-" * 80)

    all_passed = True

    for seq_no, expected, description in test_cases:
        actual = get_seq_coefficient(seq_no)
        status = "✓ PASS" if actual == expected else "✗ FAIL"

        if actual != expected:
            all_passed = False
            result['errors'].append(
                f"SEQ {seq_no}: Expected {expected}, got {actual}"
            )

        result['output'].append(
            f"{seq_no:<12} {expected:<12.1f} {actual:<12.1f} {status:<12} {description[:30]:<30}"
        )

    result['output'].append("-" * 80)
    result['output'].append("")

    if all_passed:
        result['output'].append("✓ ALL COEFFICIENT TESTS PASSED!")
        result['passed'] = True
    else:
        result['output'].append("✗ SOME COEFFICIENT TESTS FAILED!")
        result['passed'] = False

    # Test man-hour calculations
    result['output'].append("")
    result['output'].append("Testing Man-Hour Calculations:")
    result['output'].append("-" * 80)

    base_manhours = 400
    calculation_tests = [
        ("2.1", 2.0, base_manhours * 2.0, "SEQ 2.x: 400 hrs × 2.0 = 800 hrs"),
        ("3.5", 2.0, base_manhours * 2.0, "SEQ 3.x: 400 hrs × 2.0 = 800 hrs"),
        ("4.1", 1.0, base_manhours * 1.0, "SEQ 4.x: 400 hrs × 1.0 = 400 hrs"),
        ("1.1", 1.0, base_manhours * 1.0, "Other SEQ: 400 hrs × 1.0 = 400 hrs"),
    ]

    result['output'].append(f"Base Man-Hours: {base_manhours} (e.g., 5 workers × 8 hrs/day × 10 days)")
    result['output'].append("")
    result['output'].append(
        f"{'SEQ':<8} {'Coefficient':<12} {'Base Hours':<12} {'Adjusted Hours':<15} {'Description':<30}")
    result['output'].append("-" * 80)

    for seq_no, expected_coeff, expected_result, description in calculation_tests:
        coeff = get_seq_coefficient(seq_no)
        adjusted = base_manhours * coeff

        result['output'].append(
            f"{seq_no:<8} {coeff:<12.1f} {base_manhours:<12.0f} {adjusted:<15.0f} {description:<30}"
        )

        if adjusted != expected_result:
            result['errors'].append(
                f"Calculation error for SEQ {seq_no}: Expected {expected_result}, got {adjusted}"
            )
            result['passed'] = False

    result['output'].append("-" * 80)

    # Show configured coefficients
    result['output'].append("")
    result['output'].append("Configured Coefficients:")
    result['output'].append("-" * 40)
    for key, value in SEQ_COEFFICIENTS.items():
        result['output'].append(f"{key}: {value}")
    result['output'].append(f"Default: {DEFAULT_COEFFICIENT}")
    result['output'].append("-" * 40)

    return result


def test_coefficient_edge_cases():
    """
    Test edge cases for coefficient calculations.

    Returns:
        dict: Test results
    """
    result = {
        'passed': True,
        'errors': [],
        'warnings': [],
        'output': []
    }

    edge_cases = [
        ("0.1", DEFAULT_COEFFICIENT, "Very low SEQ"),
        ("99.9", DEFAULT_COEFFICIENT, "Very high SEQ"),
        ("2.999", 2.0, "High minor version"),
        ("3.0", 2.0, "Zero minor version"),
    ]

    result['output'].append("Edge Case Tests:")
    result['output'].append("-" * 60)

    for seq_no, expected, description in edge_cases:
        try:
            actual = get_seq_coefficient(seq_no)
            if actual == expected:
                result['output'].append(f"✓ {description}: {seq_no} = {actual}")
            else:
                result['output'].append(f"✗ {description}: {seq_no} = {actual} (expected {expected})")
                result['errors'].append(f"{description} failed")
                result['passed'] = False
        except Exception as e:
            result['output'].append(f"✗ {description}: Error - {e}")
            result['errors'].append(f"{description} raised exception: {e}")
            result['passed'] = False

    return result


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING SEQ COEFFICIENT FUNCTIONALITY")
    print("=" * 80)
    print()

    result = test_coefficients()

    for output in result['output']:
        print(output)

    print()

    if result['passed']:
        print("✓ Coefficient test PASSED")
    else:
        print("✗ Coefficient test FAILED")
        for error in result['errors']:
            print(f"  ERROR: {error}")