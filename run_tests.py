"""
Test Runner Script
Quick script to run all tests with a single command
"""

from tests.test_runner import run_all_tests

if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING ALL TESTS")
    print("=" * 80)
    print()

    # Run all tests with logging
    results = run_all_tests(save_log=True, verbose=True)

    print()
    print("=" * 80)

    if results['all_passed']:
        print("✓ ALL TESTS PASSED!")
        print()
        print("The system is ready to use.")
        print("Run 'python main.py' to process your files.")
    else:
        print("✗ SOME TESTS FAILED")
        print()
        print(f"Passed: {results['passed']}/{results['total_tests']}")
        print(f"Failed: {results['failed']}/{results['total_tests']}")
        print()
        print("Please review the test log in LOG/tests/ for details.")

    print("=" * 80)