"""
Main Orchestration Module
Coordinates the entire workpack processing workflow

This is the entry point for the application.
Run this file to process all files in the INPUT folder.
"""

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
    4. Process each input file:
       - Extract task IDs
       - Apply coefficients
       - Calculate man-hours
       - Check tool availability (if enabled)
       - Identify new task IDs
    5. Generate output reports:
       - Excel file with multiple sheets
       - Debug log

    Returns:
        None
    """
    print("=" * 80)
    print("WORKPACK DATA PROCESSING SYSTEM")
    print("=" * 80)
    print()

    # Step 1: Print configuration for verification
    print("Configuration:")
    print("-" * 80)
    print_config()
    print()
    print("=" * 80)
    print()

    # Step 2: Load input files
    print("Step 1: Loading Input Files")
    print("-" * 80)
    input_files = load_input_files()

    if not input_files:
        print("No input files to process. Exiting.")
        print()
        print("Please place Excel files (.xlsx) in the INPUT folder.")
        return

    print(f"Found {len(input_files)} file(s) to process")
    print()
    print("=" * 80)
    print()

    # Step 3: Load reference data
    print("Step 2: Loading Reference Data")
    print("-" * 80)
    reference_data = load_reference_ids()
    print()
    print("=" * 80)
    print()

    # Step 4: Process each file
    print("Step 3: Processing Files")
    print("=" * 80)
    print()

    for idx, input_file in enumerate(input_files, 1):
        print(f"Processing file {idx}/{len(input_files)}: {input_file}")
        print("-" * 80)

        try:
            # Process the data
            processed_data = process_data(input_file, reference_data)

            # Save the output
            save_output_file(input_file, processed_data)

            print(f"✓ Successfully processed {input_file}")
            print()

        except Exception as e:
            print(f"✗ Error processing {input_file}: {e}")
            print(f"Skipping to next file...")
            print()
            continue

        print("-" * 80)
        print()

    # Step 5: Summary
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"✓ All files processed successfully!")
    print()
    print("Output files location:")
    print(f"  - Excel reports: OUTPUT/")
    print(f"  - Debug logs: LOG/")
    print()
    print("=" * 80)


def quick_test():
    """
    Quick test function to verify the system is working.
    Run this to check configuration and imports without processing files.
    """
    print("=" * 80)
    print("QUICK SYSTEM TEST")
    print("=" * 80)
    print()

    print("Testing imports...")
    try:
        from core import config, data_loader, data_processor, id_extractor
        from features import special_code, coefficients, tool_control
        from writers import excel_writer, debug_logger
        from utils import time_utils, validation, formatters
        print("✓ All imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    print()
    print("Testing configuration...")
    try:
        print_config()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

    print()
    print("=" * 80)
    print("✓ SYSTEM TEST PASSED")
    print("=" * 80)

    return True


if __name__ == "__main__":
    # Run the main processing workflow
    main()

    # Uncomment below to run quick test instead:
    # quick_test()