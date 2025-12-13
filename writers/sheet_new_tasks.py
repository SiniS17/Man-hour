"""
New Task IDs Sheet Module
Generates the New Task IDs sheet
"""

import pandas as pd


def create_new_task_ids_sheet(writer, report_data):
    """
    Create the New Task IDs sheet with SEQ numbers.

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    new_task_ids_df = report_data['new_task_ids_with_seq']

    if len(new_task_ids_df) == 0:
        # Create empty sheet with message
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

    # Add autofilter to headers
    worksheet.auto_filter.ref = worksheet.dimensions

    # Auto-adjust column widths
    adjust_column_widths(writer, 'New Task IDs', filtered_df)


def filter_valid_task_ids(df):
    """
    Filter out None and 'nan' values from task IDs.

    Args:
        df (pd.DataFrame): DataFrame with task IDs

    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    filtered_df = df[
        df['Task ID'].notna() &
        (df['Task ID'].astype(str) != 'nan')
        ].copy()

    return filtered_df


def adjust_column_widths(writer, sheet_name, df):
    """
    Auto-adjust column widths for better readability.

    Args:
        writer: pd.ExcelWriter object
        sheet_name (str): Name of the sheet
        df (pd.DataFrame): DataFrame written to sheet
    """
    worksheet = writer.sheets[sheet_name]

    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2


def count_new_task_ids(new_task_ids_df):
    """
    Count the number of valid new task IDs.

    Args:
        new_task_ids_df (pd.DataFrame): DataFrame with new task IDs

    Returns:
        int: Count of valid new task IDs
    """
    filtered_df = filter_valid_task_ids(new_task_ids_df)
    return len(filtered_df)


def get_new_task_ids_summary(new_task_ids_df):
    """
    Generate a summary of new task IDs.

    Args:
        new_task_ids_df (pd.DataFrame): DataFrame with new task IDs

    Returns:
        dict: Summary statistics
    """
    filtered_df = filter_valid_task_ids(new_task_ids_df)

    if len(filtered_df) == 0:
        return {
            'total_new_ids': 0,
            'unique_seqs': 0
        }

    return {
        'total_new_ids': len(filtered_df),
        'unique_seqs': filtered_df.iloc[:, 0].nunique()  # First column is SEQ
    }