"""
Main Orchestration Module
Coordinates the entire workpack processing workflow
REFACTORED: Now uses centralized logging system
"""

from utils.logger import WorkpackLogger, info, error, warning
from core.config import print_config
from core.data_loader import load_input_files, load_reference_ids
from core.data_processor import process_data
from writers.excel_writer import save_output_file


def main():
    """
    Main orchestration function - coordinates the complete workflow.

    Workflow:
    1. Print and verify configuration
    2. Load input files from INPUT folder
    3. Load reference data (Task IDs and EO IDs)
    4. Process each input file
    5. Generate output reports

    Returns:
        None
    """
    # Initialize logging system
    wl = WorkpackLogger()

    info("="*80)
    info("WORKPACK DATA PROCESSING SYSTEM")
    info("="*80)
    info("")

    # Step 1: Print configuration for verification
    info("Configuration:")
    info("-"*80)
    print_config()
    info("")
    info("="*80)
    info("")

    # Step 2: Load input files
    info("Step 1: Loading Input Files")
    info("-"*80)
    input_files = load_input_files()

    if not input_files:
        error("No input files to process. Exiting.")
        info("")
        info("Please place Excel files (.xlsx) in the INPUT folder.")
        return

    info(f"Found {len(input_files)} file(s) to process")
    info("")
    info("="*80)
    info("")

    # Step 3: Load reference data
    info("Step 2: Loading Reference Data")
    info("-"*80)
    reference_data = load_reference_ids()
    info("")
    info("="*80)
    info("")

    # Step 4: Process each file
    info("Step 3: Processing Files")
    info("="*80)
    info("")

    successful_count = 0
    failed_count = 0

    for idx, input_file in enumerate(input_files, 1):
        info(f"Processing file {idx}/{len(input_files)}: {input_file}")
        info("-"*80)

        try:
            # Process the data
            processed_data = process_data(input_file, reference_data)

            # Save the output
            save_output_file(input_file, processed_data)

            info(f"✓ Successfully processed {input_file}")
            info("")
            successful_count += 1

        except Exception as e:
            error(f"✗ Error processing {input_file}: {e}")
            error(f"Skipping to next file...")
            info("")
            failed_count += 1
            continue

        info("-"*80)
        info("")

    # Step 5: Summary
    info("="*80)
    info("PROCESSING COMPLETE")
    info("="*80)
    info("")

    if failed_count == 0:
        info(f"✓ All {successful_count} file(s) processed successfully!")
    else:
        warning(f"Completed with {successful_count} successful, {failed_count} failed")

    info("")
    info("Output files location:")
    info("  - Excel reports: OUTPUT/")
    info("  - Processing logs: LOG/")
    info("")
    info("="*80)


def quick_test():
    """
    Quick test function to verify the system is working.
    Run this to check configuration and imports without processing files.
    """
    info("="*80)
    info("QUICK SYSTEM TEST")
    info("="*80)
    info("")

    info("Testing imports...")
    try:
        from core import config, data_loader, data_processor, id_extractor
        from features import special_code, type_coefficient, tool_control
        from writers import excel_writer
        from utils import time_utils, validation, formatters, logger
        info("✓ All imports successful")
    except ImportError as e:
        error(f"✗ Import error: {e}")
        return False

    info("")
    info("Testing configuration...")
    try:
        print_config()
        info("✓ Configuration loaded successfully")
    except Exception as e:
        error(f"✗ Configuration error: {e}")
        return False

    info("")
    info("Testing logging system...")
    try:
        from utils.logger import get_logger
        test_logger = get_logger(module_name="test")
        test_logger.info("Test message")
        info("✓ Logging system working")
    except Exception as e:
        error(f"✗ Logging system error: {e}")
        return False

    info("")
    info("="*80)
    info("✓ SYSTEM TEST PASSED")
    info("="*80)

    return True


if __name__ == "__main__":
    # Run the main processing workflow
    main()

    # Uncomment below to run quick test instead:
    # quick_test()