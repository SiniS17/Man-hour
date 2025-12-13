"""
Tool Control Sheet Module
Generates the Tool Control sheet showing tools/spares with zero availability
"""

import pandas as pd


def create_tool_control_sheet(writer, report_data):
    """
    Create the Tool Control sheet showing tools/spares with zero availability.

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    tool_issues_df = report_data.get('tool_control_issues', pd.DataFrame())

    if len(tool_issues_df) == 0:
        # Create empty sheet with message
        df = pd.DataFrame([['All tools and spares have adequate availability (quantity > 0)']])
        df.to_excel(writer, sheet_name='Tool Control', index=False, header=False)
        return

    # Write to Excel with headers
    tool_issues_df.to_excel(writer, sheet_name='Tool Control', index=False)

    # Get the worksheet
    worksheet = writer.sheets['Tool Control']

    # Add autofilter to headers
    worksheet.auto_filter.ref = worksheet.dimensions

    # Auto-adjust column widths
    adjust_column_widths(writer, 'Tool Control', tool_issues_df)


def adjust_column_widths(writer, sheet_name, df):
    """
    Auto-adjust column widths for better readability.
    Different columns have different max widths based on content type.

    Args:
        writer: pd.ExcelWriter object
        sheet_name (str): Name of the sheet
        df (pd.DataFrame): DataFrame written to sheet
    """
    worksheet = writer.sheets[sheet_name]

    # Define max widths for different column types
    column_max_widths = {
        'Tool/Spare Name': 70,
        'Part Number': 25,
        'Task ID': 30,
        'SEQ': 20,
        'Type': 20
    }

    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(str(col))
        )

        # Get appropriate max width for this column
        max_width = column_max_widths.get(col, 20)

        # Set width
        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, max_width)


def get_tool_control_summary(tool_issues_df):
    """
    Generate a summary of tool control issues.

    Args:
        tool_issues_df (pd.DataFrame): DataFrame with tool control issues

    Returns:
        dict: Summary statistics
    """
    if len(tool_issues_df) == 0:
        return {
            'total_issues': 0,
            'tools': 0,
            'spares': 0,
            'unique_parts': 0,
            'affected_seqs': 0
        }

    return {
        'total_issues': len(tool_issues_df),
        'tools': len(tool_issues_df[tool_issues_df['Type'] == 'Tool']),
        'spares': len(tool_issues_df[tool_issues_df['Type'] == 'Spare']),
        'unique_parts': tool_issues_df['Part Number'].nunique() if 'Part Number' in tool_issues_df.columns else 0,
        'affected_seqs': tool_issues_df['SEQ'].nunique() if 'SEQ' in tool_issues_df.columns else 0
    }


def format_tool_control_message():
    """
    Format the message for when no tool control issues are found.

    Returns:
        str: Formatted message
    """
    return 'All tools and spares have adequate availability (quantity > 0)'


def count_tool_issues_by_type(tool_issues_df):
    """
    Count tool issues by type (Tool vs Spare).

    Args:
        tool_issues_df (pd.DataFrame): DataFrame with tool control issues

    Returns:
        dict: Dictionary with counts by type
    """
    if len(tool_issues_df) == 0:
        return {'Tool': 0, 'Spare': 0, 'Unknown': 0}

    type_counts = tool_issues_df['Type'].value_counts().to_dict()

    # Ensure all types are present
    result = {
        'Tool': type_counts.get('Tool', 0),
        'Spare': type_counts.get('Spare', 0),
        'Unknown': type_counts.get('Unknown', 0)
    }

    return result