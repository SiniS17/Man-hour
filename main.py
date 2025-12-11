from input_output import load_input_files, save_output_file
from data_processing import process_data
from config import (REFERENCE_FILE, REFERENCE_FOLDER, print_config,
                    REFERENCE_TASK_SHEET_NAME, REFERENCE_TASK_ID_COLUMN,
                    REFERENCE_EO_SHEET_NAME, REFERENCE_EO_ID_COLUMN)
import os
import pandas as pd


def load_reference_ids():
    """
    Load reference IDs from both Task and EO sheets.
    Returns a tuple: (task_ids_set, eo_ids_set)
    """
    # Correctly join the REFERENCE folder with the reference file
    reference_file_path = os.path.join(REFERENCE_FOLDER, REFERENCE_FILE)

    # Load Task IDs from the Task sheet
    try:
        task_df = pd.read_excel(reference_file_path, engine='openpyxl', sheet_name=REFERENCE_TASK_SHEET_NAME)

        # Check if the column exists
        if REFERENCE_TASK_ID_COLUMN not in task_df.columns:
            print(f"WARNING: Column '{REFERENCE_TASK_ID_COLUMN}' not found in '{REFERENCE_TASK_SHEET_NAME}' sheet.")
            print(f"Available columns: {list(task_df.columns)}")
            task_ids = set()
        else:
            task_ids = task_df[REFERENCE_TASK_ID_COLUMN].dropna().apply(str).unique()
            task_ids = set(task_ids)
            print(f"Loaded {len(task_ids)} Task IDs from '{REFERENCE_TASK_SHEET_NAME}' sheet")
    except Exception as e:
        print(f"ERROR loading Task sheet: {e}")
        task_ids = set()

    # Load EO IDs from the EO sheet
    try:
        eo_df = pd.read_excel(reference_file_path, engine='openpyxl', sheet_name=REFERENCE_EO_SHEET_NAME)

        # Check if the column exists
        if REFERENCE_EO_ID_COLUMN not in eo_df.columns:
            print(f"WARNING: Column '{REFERENCE_EO_ID_COLUMN}' not found in '{REFERENCE_EO_SHEET_NAME}' sheet.")
            print(f"Available columns: {list(eo_df.columns)}")
            eo_ids = set()
        else:
            eo_ids = eo_df[REFERENCE_EO_ID_COLUMN].dropna().apply(str).unique()
            eo_ids = set(eo_ids)
            print(f"Loaded {len(eo_ids)} EO IDs from '{REFERENCE_EO_SHEET_NAME}' sheet")
    except Exception as e:
        print(f"ERROR loading EO sheet: {e}")
        eo_ids = set()

    return task_ids, eo_ids


def main():
    # Print config to verify it's loaded correctly
    print_config()
    print("\n" + "=" * 60 + "\n")

    # Step 1: Load input files
    input_files = load_input_files()

    if not input_files:
        print("No input files to process. Exiting.")
        return

    # Step 2: Load reference IDs from both sheets
    reference_task_ids, reference_eo_ids = load_reference_ids()

    print("\n" + "=" * 60 + "\n")

    # Step 3: Process each file
    for input_file in input_files:
        print(f"Processing file: {input_file}")

        # Read and process the input file (data processing logic in data_processing.py)
        processed_data = process_data(input_file, reference_task_ids, reference_eo_ids)

        # Step 4: Save the output
        save_output_file(input_file, processed_data)

        print("\n" + "-" * 60 + "\n")

    print("All files processed successfully!")


if __name__ == "__main__":
    main()