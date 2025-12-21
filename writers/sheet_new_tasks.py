"""
New Task IDs Sheet Module
FIXED: Added red highlighting for blank SEQ rows
"""

import pandas as pd
from openpyxl.styles import PatternFill


def create_new_task_ids_sheet(writer, report_data):
    """
    Create the New Task IDs sheet with SEQ numbers.
    FIXED: Added red highlighting for blank SEQ rows.
    """
    new_task_ids_df = report_data['new_task_ids_with_seq']

    if len(new_task_ids_df) == 0:
        df = pd.DataFrame([['No new task IDs found - all task IDs match reference']])
        df.to_excel(writer, sheet_name='New Task IDs', index=False, header=False)
        return

    # Filter out None and 'nan' values
    filtered_df = filter_valid_task_ids(new_task_ids_df)

    if len(filtered_df) == 0:
        df = pd.DataFrame([['No new task IDs found - all task IDs match reference']])
        df.to_excel(writer, sheet_name='New Task IDs', index=False, header=False)
        return

    # Rename columns for clarity
    filtered_df.columns = ['SEQ', 'New Task ID']

    # Write to Excel
    filtered_df.to_excel(writer, sheet_name='New Task IDs', index=False)

    # Get the worksheet
    worksheet = writer.sheets['New Task IDs']
    worksheet.auto_filter.ref = worksheet.dimensions

    # Auto-adjust column widths
    adjust_column_widths(writer, 'New Task IDs', filtered_df)

    # Add red highlighting for blank SEQ rows
    highlight_blank_seq_rows(worksheet, filtered_df)


def highlight_blank_seq_rows(worksheet, df):
    """
    Add red highlighting to rows with blank SEQ values.

    Args:
        worksheet: openpyxl worksheet object
        df: DataFrame that was written to the sheet
    """
    red_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")

    # SEQ is the first column (index 0)
    seq_col_idx = 0

    # Check each data row (starting from row 2, after header)
    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        seq_value = row['SEQ']

        # Check if SEQ is blank/empty
        if pd.isna(seq_value) or str(seq_value).strip() == '':
            # Highlight entire row
            for col_idx in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                cell.fill = red_fill


def filter_valid_task_ids(df):
    """Filter out None and 'nan' values from task IDs."""
    filtered_df = df[
        df['Task ID'].notna() &
        (df['Task ID'].astype(str) != 'nan')
    ].copy()
    return filtered_df


def adjust_column_widths(writer, sheet_name, df):
    """Auto-adjust column widths for better readability."""
    worksheet = writer.sheets[sheet_name]

    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2


def count_new_task_ids(new_task_ids_df):
    """Count the number of valid new task IDs."""
    filtered_df = filter_valid_task_ids(new_task_ids_df)
    return len(filtered_df)


def get_new_task_ids_summary(new_task_ids_df):
    """Generate a summary of new task IDs."""
    filtered_df = filter_valid_task_ids(new_task_ids_df)

    if len(filtered_df) == 0:
        return {
            'total_new_ids': 0,
            'unique_seqs': 0
        }

    return {
        'total_new_ids': len(filtered_df),
        'unique_seqs': filtered_df.iloc[:, 0].nunique()
    }