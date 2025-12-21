"""
High Man-Hours Sheet Module
UPDATED: Removed decimal hours, shows coefficient instead of type coefficient
"""

import pandas as pd
from utils.time_utils import hours_to_hhmm
from core.config import SEQ_NO_COLUMN, TITLE_COLUMN


def create_high_mhrs_sheet(writer, report_data):
    """
    Create the High Man-Hours Tasks sheet with SEQ coefficient info.
    """
    high_mhrs_df = report_data['high_mhrs_tasks'].copy()

    if len(high_mhrs_df) == 0:
        df = pd.DataFrame([['No tasks found with planned man-hours exceeding the threshold']])
        df.to_excel(writer, sheet_name='High Man-Hours Tasks', index=False, header=False)
        return

    # Add HH:MM formatted column (Base Hours only)
    high_mhrs_df['Base Mhrs'] = high_mhrs_df['Base Hours'].apply(hours_to_hhmm)

    # Select and order columns
    columns_to_export = build_export_columns(high_mhrs_df)
    export_df = high_mhrs_df[columns_to_export]

    # Write to Excel
    export_df.to_excel(writer, sheet_name='High Man-Hours Tasks', index=False)

    # Get the worksheet
    worksheet = writer.sheets['High Man-Hours Tasks']
    worksheet.auto_filter.ref = worksheet.dimensions

    # Auto-adjust column widths
    adjust_column_widths(writer, 'High Man-Hours Tasks', export_df)


def build_export_columns(df):
    """Build the list of columns to export."""
    columns_to_export = []

    if SEQ_NO_COLUMN in df.columns:
        columns_to_export.append(SEQ_NO_COLUMN)

    if TITLE_COLUMN in df.columns:
        columns_to_export.append(TITLE_COLUMN)

    if 'Task ID' in df.columns:
        columns_to_export.append('Task ID')

    # Add Base Hours column only (HH:MM format)
    columns_to_export.append('Base Mhrs')

    return columns_to_export


def adjust_column_widths(writer, sheet_name, df, max_width=50):
    """Auto-adjust column widths."""
    worksheet = writer.sheets[sheet_name]

    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, max_width)