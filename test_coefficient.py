"""
Test script to verify SEQ coefficient functionality
"""
from config import get_seq_coefficient, print_config


def test_seq_coefficients():
    """Test the coefficient retrieval for different SEQ values"""

    print("=" * 60)
    print("TESTING SEQ COEFFICIENT FUNCTIONALITY")
    print("=" * 60)
    print()

    # Test cases: (seq_no, expected_coefficient)
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

    print("Test Cases:")
    print("-" * 60)
    print(f"{'SEQ No.':<12} {'Expected':<12} {'Actual':<12} {'Status':<12} {'Description':<30}")
    print("-" * 60)

    all_passed = True

    for seq_no, expected, description in test_cases:
        actual = get_seq_coefficient(seq_no)
        status = "✓ PASS" if actual == expected else "✗ FAIL"

        if actual != expected:
            all_passed = False

        print(f"{seq_no:<12} {expected:<12.1f} {actual:<12.1f} {status:<12} {description[:30]:<30}")

    print("-" * 60)
    print()

    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED!")

    print()
    print("=" * 60)
    print()


def test_manhour_calculation():
    """Test actual man-hour calculations with coefficients"""

    print("=" * 60)
    print("TESTING MAN-HOUR CALCULATIONS WITH COEFFICIENTS")
    print("=" * 60)
    print()

    # Example: 5 workers, 8 hours/day, 10 days = 400 man-hours base
    base_manhours = 400

    test_scenarios = [
        ("2.1", 2.0, base_manhours * 2.0, "SEQ 2.x: 400 hrs × 2.0 = 800 hrs"),
        ("3.5", 2.0, base_manhours * 2.0, "SEQ 3.x: 400 hrs × 2.0 = 800 hrs"),
        ("4.1", 1.0, base_manhours * 1.0, "SEQ 4.x: 400 hrs × 1.0 = 400 hrs"),
        ("1.1", 1.0, base_manhours * 1.0, "Other SEQ: 400 hrs × 1.0 = 400 hrs"),
    ]

    print(f"Base Man-Hours: {base_manhours} (e.g., 5 workers × 8 hrs/day × 10 days)")
    print()
    print("-" * 80)
    print(f"{'SEQ':<8} {'Coefficient':<12} {'Base Hours':<12} {'Adjusted Hours':<15} {'Description':<30}")
    print("-" * 80)

    for seq_no, expected_coeff, expected_result, description in test_scenarios:
        coeff = get_seq_coefficient(seq_no)
        adjusted = base_manhours * coeff

        print(f"{seq_no:<8} {coeff:<12.1f} {base_manhours:<12.0f} {adjusted:<15.0f} {description:<30}")

    print("-" * 80)
    print()
    print("=" * 60)
    print()


if __name__ == "__main__":
    # First show the configuration
    print("\nCurrent Configuration:")
    print("=" * 60)
    print_config()
    print("=" * 60)
    print("\n")

    # Run tests
    test_seq_coefficients()
    test_manhour_calculation()

    print("\nTest complete! If all tests passed, the coefficient system is working correctly.")
    print("You can now run main.py to process your actual data files.\n")