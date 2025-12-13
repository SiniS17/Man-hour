"""
High Man-Hours Sheet Module
Generates the High Man-Hours Tasks sheet
"""

import pandas as pd
from utils.time_utils import hours_to_hhmm
from core.config import SEQ_NO_COLUMN, TITLE_COLUMN


def create_high_mhrs_sheet(writer, report_data):
    """
    Create the High Man-Hours Tasks sheet with coefficient info.

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    high_mhrs_df = report_data['high_mhrs_tasks'].copy()

    if len(high_mhrs_df) == 0:
        # Create empty sheet with message
        df = pd.DataFrame([['No tasks found with planned man-hours exceeding the threshold']])
        df.to_excel(writer, sheet_name='High Man-Hours Tasks', index=False, header=False)
        return

    # Add HH:MM formatted columns for both base and adjusted hours
    high_mhrs_df['Base Mhrs (HH:MM)'] = high_mhrs_df['Base Hours'].apply(hours_to_hhmm)
    high_mhrs_df['Adjusted Mhrs (HH:MM)'] = high_mhrs_df['Adjusted Hours'].apply(hours_to_hhmm)

    # Select and order columns
    columns_to_export = build_export_columns(high_mhrs_df)
    export_df = high_mhrs_df[columns_to_export]

    # Write to Excel
    export_df.to_excel(writer, sheet_name='High Man-Hours Tasks', index=False)

    # Get the worksheet
    worksheet = writer.sheets['High Man-Hours Tasks']

    # Add autofilter to headers
    worksheet.auto_filter.ref = worksheet.dimensions

    # Auto-adjust column widths
    adjust_column_widths(writer, 'High Man-Hours Tasks', export_df)


def build_export_columns(df):
    """
    Build the list of columns to export based on what's available.

    Args:
        df (pd.DataFrame): DataFrame to export

    Returns:
        list: List of column names to export
    """
    columns_to_export = []

    # Add SEQ_NO_COLUMN if it exists
    if SEQ_NO_COLUMN in df.columns:
        columns_to_export.append(SEQ_NO_COLUMN)

    # Add TITLE_COLUMN if it exists
    if TITLE_COLUMN in df.columns:
        columns_to_export.append(TITLE_COLUMN)

    # Add Task ID if it exists
    if 'Task ID' in df.columns:
        columns_to_export.append('Task ID')

    # Add coefficient and hour columns
    columns_to_export.extend(['Coefficient', 'Base Mhrs (HH:MM)', 'Adjusted Mhrs (HH:MM)'])

    return columns_to_export


def adjust_column_widths(writer, sheet_name, df, max_width=50):
    """
    Auto-adjust column widths for better readability.

    Args:
        writer: pd.ExcelWriter object
        sheet_name (str): Name of the sheet
        df (pd.DataFrame): DataFrame written to sheet
        max_width (int): Maximum column width
    """
    worksheet = writer.sheets[sheet_name]

    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, max_width)


def format_high_mhrs_message(threshold):
    """
    Format the message for when no high man-hours tasks are found.

    Args:
        threshold (int): Man-hours threshold

    Returns:
        str: Formatted message
    """
    return f"No tasks found with planned man-hours exceeding {threshold} hours"