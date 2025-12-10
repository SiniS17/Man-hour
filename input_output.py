import os
import pandas as pd
import glob
from datetime import datetime
from config import INPUT_FOLDER, OUTPUT_FOLDER


# Load all Excel files from the input folder
def load_input_files():
    input_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))
    if not input_files:
        print(f"No .xlsx files found in the '{INPUT_FOLDER}' folder.")
    return input_files


# Save the processed data to an output folder
def save_output_file(input_file_name, data):
    # Create a subfolder for each input file
    base_filename = os.path.splitext(os.path.basename(input_file_name))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(OUTPUT_FOLDER, base_filename)
    os.makedirs(output_folder, exist_ok=True)

    # Define output text file path
    output_txt_path = os.path.join(output_folder, f"{base_filename}_{timestamp}.txt")

    # Write the processed data to a text file
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"Output saved to {output_txt_path}")
