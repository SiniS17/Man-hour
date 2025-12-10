from input_output import load_input_files, save_output_file
from data_processing import process_data
from config import REFERENCE_FILE, REFERENCE_FOLDER, print_config
import os
import pandas as pd


def load_reference_ids():
    # Correctly join the REFERENCE folder with the reference file
    reference_file_path = os.path.join(REFERENCE_FOLDER, REFERENCE_FILE)

    # Load the reference file
    reference_df = pd.read_excel(reference_file_path, engine='openpyxl', sheet_name='List item')

    # Extract the task IDs (J0BCARD) from the reference file
    reference_ids = reference_df['J0BCARD'].dropna().apply(str).unique()
    return set(reference_ids)


def main():
    # Print config to verify it's loaded correctly
    print_config()

    # Step 1: Load input files
    input_files = load_input_files()

    # Step 2: Load reference IDs
    reference_ids = load_reference_ids()

    # Step 3: Process each file
    for input_file in input_files:
        print(f"Processing file: {input_file}")

        # Read and process the input file (data processing logic in data_processing.py)
        processed_data = process_data(input_file, reference_ids)

        # Step 4: Save the output
        save_output_file(input_file, processed_data)


if __name__ == "__main__":
    main()
