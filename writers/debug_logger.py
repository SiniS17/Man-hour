"""
Debug Logger Module
Handles debug log generation and writing
"""

import os
import pandas as pd
from datetime import datetime
from utils.time_utils import hours_to_hhmm
from core.config import SEQ_NO_COLUMN, TITLE_COLUMN


def save_debug_log(base_filename, timestamp, report_data):
    """
    Save debug information to LOG folder.

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

    # Define log file path
    log_file_path = os.path.join(file_log_folder, f"debug_{timestamp}.txt")

    # Write debug information
    with open(log_file_path, "w", encoding="utf-8") as f:
        write_debug_header(f, base_filename, report_data)
        write_debug_sample(f, report_data)

    print(f"Debug log saved to {log_file_path}")


def write_debug_header(f, base_filename, report_data):
    """
    Write the header section of the debug log.

    Args:
        f: File object
        base_filename (str): Base name of input file
        report_data (dict): Dictionary containing processed data
    """
    f.write("=" * 60 + "\n")
    f.write("DEBUG LOG\n")
    f.write("=" * 60 + "\n")
    f.write(f"File: {base_filename}\n")
    f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Add workpack info if available
    if report_data.get('start_date') and report_data.get('end_date'):
        f.write(
            f"Workpack Period: {report_data['start_date'].strftime('%Y-%m-%d')} to {report_data['end_date'].strftime('%Y-%m-%d')}\n")
        f.write(f"Workpack Duration: {report_data.get('workpack_days', 'N/A')} days\n")

    # Add man-hours summary
    f.write("\nMan-Hours Summary:\n")
    f.write(f"Base Man-Hours: {report_data.get('total_base_mhrs_hhmm', 'N/A')}\n")
    f.write(f"Adjusted Man-Hours (with coefficients): {report_data['total_mhrs_hhmm']}\n")

    f.write("=" * 60 + "\n\n")


def write_debug_sample(f, report_data):
    """
    Write the debug sample section showing random rows.

    Args:
        f: File object
        report_data (dict): Dictionary containing processed data
    """
    debug_df = report_data['debug_sample']

    if len(debug_df) == 0:
        f.write("No data to display (all rows were ignored)\n")
        return

    f.write(f"DEBUG SAMPLE REPORT (Random {len(debug_df)} Rows):\n")
    f.write("-" * 110 + "\n")

    if report_data['enable_special_code']:
        write_debug_sample_with_special_code(f, debug_df)
    else:
        write_debug_sample_without_special_code(f, debug_df)

    f.write("-" * 110 + "\n")


def write_debug_sample_with_special_code(f, debug_df):
    """
    Write debug sample with special code column.

    Args:
        f: File object
        debug_df (pd.DataFrame): Debug sample DataFrame
    """
    f.write(f"| {SEQ_NO_COLUMN:<8} | Special Code | Task ID          | Coeff | Base Mhrs | Adjusted Mhrs |\n")
    f.write("-" * 110 + "\n")

    for index, row in debug_df.iterrows():
        seq_no = str(row[SEQ_NO_COLUMN])
        special_code = str(row.get('Special code', 'N/A')) if pd.notna(row.get('Special code')) else "N/A"
        special_code = special_code[:12]
        task_id = str(row['Task ID'])[:16]
        coefficient = row.get('Coefficient', 1.0)
        base_hours = row.get('Base Hours', 0)
        adjusted_hours = row.get('Adjusted Hours', 0)
        base_time_hhmm = hours_to_hhmm(base_hours)
        adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

        f.write(
            f"| {seq_no:<8} | {special_code:<12} | {task_id:<16} | {coefficient:<5.1f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |\n")


def write_debug_sample_without_special_code(f, debug_df):
    """
    Write debug sample without special code column.

    Args:
        f: File object
        debug_df (pd.DataFrame): Debug sample DataFrame
    """
    f.write(
        f"| {SEQ_NO_COLUMN:<8} | {TITLE_COLUMN[:30]:<30} | Task ID          | Coeff | Base Mhrs | Adjusted Mhrs |\n")
    f.write("-" * 115 + "\n")

    for index, row in debug_df.iterrows():
        seq_no = str(row[SEQ_NO_COLUMN])
        title = str(row[TITLE_COLUMN])[:30]
        task_id = str(row['Task ID'])[:16]
        coefficient = row.get('Coefficient', 1.0)
        base_hours = row.get('Base Hours', 0)
        adjusted_hours = row.get('Adjusted Hours', 0)
        base_time_hhmm = hours_to_hhmm(base_hours)
        adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

        f.write(
            f"| {seq_no:<8} | {title:<30} | {task_id:<16} | {coefficient:<5.1f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |\n")


def format_debug_row(row, include_special_code=False):
    """
    Format a single row for debug output.

    Args:
        row: DataFrame row
        include_special_code (bool): Whether to include special code column

    Returns:
        str: Formatted row string
    """
    seq_no = str(row[SEQ_NO_COLUMN])
    task_id = str(row.get('Task ID', 'N/A'))[:16]
    coefficient = row.get('Coefficient', 1.0)
    base_hours = row.get('Base Hours', 0)
    adjusted_hours = row.get('Adjusted Hours', 0)
    base_time_hhmm = hours_to_hhmm(base_hours)
    adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)

    if include_special_code:
        special_code = str(row.get('Special code', 'N/A')) if pd.notna(row.get('Special code')) else "N/A"
        special_code = special_code[:12]
        return f"| {seq_no:<8} | {special_code:<12} | {task_id:<16} | {coefficient:<5.1f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |"
    else:
        title = str(row[TITLE_COLUMN])[:30]
        return f"| {seq_no:<8} | {title:<30} | {task_id:<16} | {coefficient:<5.1f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |"


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