"""
Debug Logger Module
Handles debug log generation and writing
Now includes ALL debug output, not just sample data
"""

import os
import pandas as pd
from datetime import datetime
from utils.time_utils import hours_to_hhmm
from core.config import SEQ_NO_COLUMN, TITLE_COLUMN


class DebugLogger:
    """
    Centralized debug logger that writes to both console and log file
    """
    def __init__(self, base_filename, timestamp):
        """
        Initialize debug logger

        Args:
            base_filename: Base name of input file
            timestamp: Timestamp string
        """
        self.base_filename = base_filename
        self.timestamp = timestamp
        self.log_file_path = None
        self.log_file = None

    def __enter__(self):
        """Context manager entry - open log file"""
        # Create LOG folder structure
        log_folder = os.path.join(os.getcwd(), 'LOG')
        os.makedirs(log_folder, exist_ok=True)

        file_log_folder = os.path.join(log_folder, self.base_filename)
        os.makedirs(file_log_folder, exist_ok=True)

        # Open log file for writing
        self.log_file_path = os.path.join(file_log_folder, f"debug_{self.timestamp}.txt")
        self.log_file = open(self.log_file_path, "w", encoding="utf-8")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close log file"""
        if self.log_file:
            self.log_file.close()
            print(f"\n✓ Debug log saved to {self.log_file_path}")

    def log(self, message, to_console=True):
        """
        Write message to both log file and console

        Args:
            message: Message to write
            to_console: Whether to also print to console (default True)
        """
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()  # Ensure immediate write

        if to_console:
            print(message)

    def log_separator(self, char="=", length=80):
        """Write a separator line"""
        self.log(char * length)

    def log_header(self, title):
        """Write a formatted header"""
        self.log_separator()
        self.log(title)
        self.log_separator()


def save_debug_log(base_filename, timestamp, report_data):
    """
    Save debug information to LOG folder.
    This is called at the end to write the sample data.

    Args:
        base_filename (str): Base name of input file
        timestamp (str): Timestamp string
        report_data (dict): Dictionary containing processed data
    """
    # Create LOG folder in root directory
    log_folder = os.path.join(os.getcwd(), 'LOG')
    os.makedirs(log_folder, exist_ok=True)

    # Create subfolder for this file
    file_log_folder = os.path.join(log_folder, base_filename)
    os.makedirs(file_log_folder, exist_ok=True)

    # Define log file path - append to existing file
    log_file_path = os.path.join(file_log_folder, f"debug_{timestamp}.txt")

    # Append debug information
    with open(log_file_path, "a", encoding="utf-8") as f:
        write_debug_sample(f, report_data)


def write_debug_sample(f, report_data):
    """
    Write the debug sample section showing random rows.

    Args:
        f: File object
        report_data (dict): Dictionary containing processed data
    """
    debug_df = report_data['debug_sample']

    f.write("\n\n")
    f.write("=" * 80 + "\n")
    f.write("DEBUG SAMPLE REPORT\n")
    f.write("=" * 80 + "\n")

    if len(debug_df) == 0:
        f.write("No data to display (all rows were ignored)\n")
        return

    f.write(f"Random Sample ({len(debug_df)} Rows):\n")
    f.write("-" * 120 + "\n")

    if report_data['enable_special_code']:
        write_debug_sample_with_special_code(f, debug_df)
    else:
        write_debug_sample_without_special_code(f, debug_df)

    f.write("-" * 120 + "\n")


def write_debug_sample_with_special_code(f, debug_df):
    """
    Write debug sample with special code column.

    Args:
        f: File object
        debug_df (pd.DataFrame): Debug sample DataFrame
    """
    f.write(f"| {SEQ_NO_COLUMN:<8} | Special Code | Task ID          | Type Coeff | Base Mhrs | Adjusted Mhrs |\n")
    f.write("-" * 120 + "\n")

    for index, row in debug_df.iterrows():
        seq_no = str(row[SEQ_NO_COLUMN])
        special_code = str(row.get('Special code', 'N/A')) if pd.notna(row.get('Special code')) else "N/A"
        special_code = special_code[:12]
        task_id = str(row['Task ID'])[:16]
        type_coefficient = row.get('Type Coefficient', 1.0)
        base_hours = row.get('Base Hours', 0)
        adjusted_hours = row.get('Adjusted Hours', 0)
        base_time_hhmm = hours_to_hhmm(base_hours)
        adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

        f.write(
            f"| {seq_no:<8} | {special_code:<12} | {task_id:<16} | {type_coefficient:<10.2f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |\n")


def write_debug_sample_without_special_code(f, debug_df):
    """
    Write debug sample without special code column.

    Args:
        f: File object
        debug_df (pd.DataFrame): Debug sample DataFrame
    """
    f.write(
        f"| {SEQ_NO_COLUMN:<8} | {TITLE_COLUMN[:30]:<30} | Task ID          | Type Coeff | Base Mhrs | Adjusted Mhrs |\n")
    f.write("-" * 125 + "\n")

    for index, row in debug_df.iterrows():
        seq_no = str(row[SEQ_NO_COLUMN])
        title = str(row[TITLE_COLUMN])[:30]
        task_id = str(row['Task ID'])[:16]
        type_coefficient = row.get('Type Coefficient', 1.0)
        base_hours = row.get('Base Hours', 0)
        adjusted_hours = row.get('Adjusted Hours', 0)
        base_time_hhmm = hours_to_hhmm(base_hours)
        adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

        f.write(
            f"| {seq_no:<8} | {title:<30} | {task_id:<16} | {type_coefficient:<10.2f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |\n")


def create_log_folder_structure(base_filename):
    """
    Create the folder structure for log files.

    Args:
        base_filename (str): Base name of input file

    Returns:
        str: Path to the log folder
    """
    log_folder = os.path.join(os.getcwd(), 'LOG')
    os.makedirs(log_folder, exist_ok=True)

    file_log_folder = os.path.join(log_folder, base_filename)
    os.makedirs(file_log_folder, exist_ok=True)

    return file_log_folder