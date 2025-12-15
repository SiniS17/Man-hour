"""
Excel Writer Module
Main orchestration for Excel output generation
"""

import os
import glob
import pandas as pd
from datetime import datetime
from core.config import INPUT_FOLDER, OUTPUT_FOLDER
from .sheet_total_mhrs import create_total_mhrs_sheet
from .sheet_high_mhrs import create_high_mhrs_sheet
from .sheet_new_tasks import create_new_task_ids_sheet
from .sheet_tool_control import create_tool_control_sheet
from .debug_logger import save_debug_log
from .sheet_bonus_hours import create_bonus_hours_sheet


def load_input_files():
    """
    Load all Excel files from the input folder.

    Returns:
        list: List of paths to input Excel files
    """
    input_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))
    if not input_files:
        print(f"No .xlsx files found in the '{INPUT_FOLDER}' folder.")
    return input_files


def save_output_file(input_file_name, report_data):
    """
    Save the report data to Excel file and debug log.

    This is the main orchestration function that:
    1. Creates output folder structure
    2. Generates Excel file with multiple sheets
    3. Saves debug log

    Args:
        input_file_name (str): Name of the input file
        report_data (dict): Dictionary containing all processed data
    """
    # Create a subfolder for each input file in OUTPUT
    base_filename = os.path.splitext(os.path.basename(input_file_name))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(OUTPUT_FOLDER, base_filename)
    os.makedirs(output_folder, exist_ok=True)

    # Define output Excel file path
    output_xlsx_path = os.path.join(output_folder, f"{base_filename}_{timestamp}.xlsx")

    # Create Excel writer
    with pd.ExcelWriter(output_xlsx_path, engine='openpyxl') as writer:
        # Sheet 1: Total Man-Hours
        create_total_mhrs_sheet(writer, report_data)

        # Sheet 2: High Man-Hours Tasks
        create_high_mhrs_sheet(writer, report_data)

        # Sheet 3: New Task IDs
        create_new_task_ids_sheet(writer, report_data)

        # Sheet 4: Bonus Hours (NEW)
        create_bonus_hours_sheet(writer, report_data)

        # Sheet 5: Tool Control (if enabled)
        if report_data.get('enable_tool_control', False):
            create_tool_control_sheet(writer, report_data)

    print(f"Excel report saved to {output_xlsx_path}")

    # Save debug log to LOG folder in root directory
    save_debug_log(base_filename, timestamp, report_data)


def create_output_folder_structure(base_filename):
    """
    Create the folder structure for output files.

    Args:
        base_filename (str): Base name of the input file

    Returns:
        str: Path to the output folder
    """
    output_folder = os.path.join(OUTPUT_FOLDER, base_filename)
    os.makedirs(output_folder, exist_ok=True)
    return output_folder


def get_output_file_path(base_filename, timestamp):
    """
    Generate the output Excel file path.

    Args:
        base_filename (str): Base name of the input file
        timestamp (str): Timestamp string

    Returns:
        str: Full path to output Excel file
    """
    output_folder = create_output_folder_structure(base_filename)
    return os.path.join(output_folder, f"{base_filename}_{timestamp}.xlsx")