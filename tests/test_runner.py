"""
Test Runner Module
Unified test orchestration with comprehensive logging
REFACTORED: Now uses centralized logging system
"""

import os
import logging
from datetime import datetime
from utils.logger import get_logger, info, error, warning
from .test_config import test_config
from .test_coefficients import test_coefficients
from .test_tool_control import test_tool_control
from .test_data_quality import test_data_quality

# Get module-specific logger
logger = get_logger(module_name="test_runner")


class TestResult:
    """Class to track test results"""

    def __init__(self, test_name):
        self.test_name = test_name
        self.passed = False
        self.failed = False
        self.errors = []
        self.warnings = []
        self.output = []

    def mark_passed(self):
        self.passed = True

    def mark_failed(self, error_msg):
        self.failed = True
        self.errors.append(error_msg)

    def add_warning(self, warning_msg):
        self.warnings.append(warning_msg)

    def add_output(self, output_msg):
        self.output.append(output_msg)

    def get_status(self):
        if self.failed:
            return "FAILED"
        elif self.warnings:
            return "PASSED (with warnings)"
        elif self.passed:
            return "PASSED"
        else:
            return "NOT RUN"


def run_all_tests(save_log=True, verbose=True):
    """
    Run all tests with comprehensive logging.

    Args:
        save_log (bool): Whether to save log to file
        verbose (bool): Whether to print detailed output

    Returns:
        dict: Dictionary with test results
    """
    # Temporarily disable logging during tests to reduce noise
    if not verbose:
        logging.disable(logging.CRITICAL)

    info("="*80)
    info("RUNNING COMPREHENSIVE TEST SUITE")
    info("="*80)
    info("")

    results = []

    # Test 1: Configuration
    info("Test 1: Configuration Validation")
    info("-"*80)
    result = run_test_with_capture(test_config, "Configuration", verbose)
    results.append(result)
    info("")

    # Test 2: Coefficients
    info("Test 2: Coefficient Functionality")
    info("-"*80)
    result = run_test_with_capture(test_coefficients, "Coefficients", verbose)
    results.append(result)
    info("")

    # Test 3: Tool Control
    info("Test 3: Tool Control Functionality")
    info("-"*80)
    result = run_test_with_capture(test_tool_control, "Tool Control", verbose)
    results.append(result)
    info("")

    # Test 4: Data Quality
    info("Test 4: Data Quality Checks")
    info("-"*80)
    result = run_test_with_capture(test_data_quality, "Data Quality", verbose)
    results.append(result)
    info("")

    # Re-enable logging
    if not verbose:
        logging.disable(logging.NOTSET)

    # Print summary
    print_test_summary(results)

    # Save log if requested
    if save_log:
        save_test_log(results)

    return {
        'results': results,
        'all_passed': all(r.passed for r in results),
        'total_tests': len(results),
        'passed': sum(1 for r in results if r.passed),
        'failed': sum(1 for r in results if r.failed)
    }


def run_test_with_capture(test_func, test_name, verbose=True):
    """
    Run a test function and capture its output.

    Args:
        test_func: Test function to run
        test_name (str): Name of the test
        verbose (bool): Whether to print output

    Returns:
        TestResult: Test result object
    """
    result = TestResult(test_name)

    try:
        # Run the test
        test_output = test_func()

        # Process return value
        if isinstance(test_output, dict):
            if test_output.get('passed', False):
                result.mark_passed()
            else:
                result.mark_failed(test_output.get('error', 'Test failed'))

            # Capture warnings
            for warn in test_output.get('warnings', []):
                result.add_warning(warn)

            # Capture output
            for out in test_output.get('output', []):
                result.add_output(out)
        else:
            result.mark_passed()

        if verbose:
            info(f"✓ {test_name} test completed successfully")

    except Exception as e:
        result.mark_failed(str(e))
        if verbose:
            error(f"✗ {test_name} test failed: {e}")

    return result


def print_test_summary(results):
    """
    Print a summary of all test results.

    Args:
        results (list): List of TestResult objects
    """
    print("")
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("")

    for result in results:
        status_symbol = "✓" if result.passed else "✗"
        status = result.get_status()
        print(f"{status_symbol} {result.test_name}: {status}")

        if result.errors:
            for err in result.errors:
                print(f"  ERROR: {err}")

        if result.warnings:
            for warn in result.warnings:
                print(f"  WARNING: {warn}")

    print("")
    print("-"*80)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if r.failed)

    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("")
        print("✓ ALL TESTS PASSED!")
    else:
        print("")
        print("✗ SOME TESTS FAILED - Please review errors above")

    print("="*80)


def save_test_log(results):
    """
    Save test results to LOG folder.

    Args:
        results (list): List of TestResult objects
    """
    # Create LOG/tests folder
    log_folder = os.path.join(os.getcwd(), 'LOG', 'tests')
    os.makedirs(log_folder, exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(log_folder, f"test_results_{timestamp}.txt")

    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write("COMPREHENSIVE TEST RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")

        # Write individual test results
        for result in results:
            f.write("-"*80 + "\n")
            f.write(f"TEST: {result.test_name}\n")
            f.write(f"STATUS: {result.get_status()}\n")
            f.write("-"*80 + "\n")

            if result.output:
                f.write("\nOutput:\n")
                for output in result.output:
                    f.write(f"  {output}\n")

            if result.errors:
                f.write("\nErrors:\n")
                for err in result.errors:
                    f.write(f"  ✗ {err}\n")

            if result.warnings:
                f.write("\nWarnings:\n")
                for warn in result.warnings:
                    f.write(f"  ⚠ {warn}\n")

            f.write("\n")

        # Write summary
        f.write("="*80 + "\n")
        f.write("SUMMARY\n")
        f.write("="*80 + "\n")

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if r.failed)

        f.write(f"Total Tests: {total}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n")

        if failed == 0:
            f.write("\n✓ ALL TESTS PASSED!\n")
        else:
            f.write("\n✗ SOME TESTS FAILED\n")

        f.write("="*80 + "\n")

    logger.info(f"Test log saved to: {log_file_path}")


def main():
    """Main function to run all tests"""
    run_all_tests(save_log=True, verbose=True)


if __name__ == "__main__":
    main()