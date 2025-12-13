"""
Tool Control Module - Separate from man-hour calculations

This module checks tool/spare availability independently.
It processes EVERY row in the input file without any deduplication,
because each row represents a different part requirement.
"""

import pandas as pd
from config import (SEQ_NO_COLUMN, TITLE_COLUMN,
                    TOOL_NAME_COLUMN, TOOL_TYPE_COLUMN, TOOL_PARTNO_COLUMN,
                    TOTAL_QTY_COLUMN, ALT_QTY_COLUMN)


def extract_task_id_for_tool_control(row, seq_mappings, seq_id_mappings):
    """
    Extract Task ID for tool control purposes.
    This is a standalone function that doesn't affect man-hour processing.

    Args:
        row: DataFrame row
        seq_mappings: SEQ mapping configuration
        seq_id_mappings: SEQ ID extraction configuration

    Returns:
        str: Extracted Task ID
    """
    seq_no = str(row[SEQ_NO_COLUMN])
    seq_prefix = seq_no.split('.')[0]

    # Get the ID extraction method
    id_mapping_key = f"SEQ_{seq_prefix}.X_ID"
    id_extraction_method = seq_id_mappings.get(id_mapping_key, "/")

    # Extract the task ID from the title
    title = str(row[TITLE_COLUMN])

    if id_extraction_method == "-":
        # Extract everything before "(" (e.g., "24-045-00 (00) - ITEM 1" -> "24-045-00")
        if "(" in title:
            id_part = title.split("(")[0].strip()
            return id_part
        else:
            return title.strip()
    elif id_extraction_method == "/":
        # Extract everything before the first "/"
        if "/" in title:
            return title.split("/")[0].strip()
        else:
            return title.strip()
    else:
        # Default: return the whole title
        return title.strip()


def check_tool_availability(df, seq_mappings, seq_id_mappings):
    """
    Check for tools/spares with zero quantity in both total_qty and altpart_total_qty.

    IMPORTANT: This function processes EVERY row independently.
    No deduplication is performed because each row represents a different part requirement,
    even if they have the same SEQ or part number.

    Args:
        df: Full DataFrame (all rows from input file)
        seq_mappings: SEQ mapping configuration
        seq_id_mappings: SEQ ID extraction configuration

    Returns:
        DataFrame with columns: SEQ, Task ID, Part Number, Tool/Spare Name, Type
    """
    # Validate required columns exist
    if not all([TOOL_NAME_COLUMN, TOOL_TYPE_COLUMN, TOOL_PARTNO_COLUMN,
                TOTAL_QTY_COLUMN, ALT_QTY_COLUMN]):
        print("WARNING: Tool control columns not properly configured in settings.ini")
        return pd.DataFrame()

    required_tool_cols = [TOOL_NAME_COLUMN, TOOL_TYPE_COLUMN, TOOL_PARTNO_COLUMN,
                          TOTAL_QTY_COLUMN, ALT_QTY_COLUMN]
    missing_cols = [col for col in required_tool_cols if col not in df.columns]

    if missing_cols:
        print(f"WARNING: Tool control columns not found in file: {missing_cols}")
        return pd.DataFrame()

    # Create a working copy to avoid modifying original
    df_tools = df.copy()

    # Convert quantity columns to numeric, treating non-numeric as 0
    df_tools[TOTAL_QTY_COLUMN] = pd.to_numeric(df_tools[TOTAL_QTY_COLUMN], errors='coerce').fillna(0)
    df_tools[ALT_QTY_COLUMN] = pd.to_numeric(df_tools[ALT_QTY_COLUMN], errors='coerce').fillna(0)

    # Filter rows where BOTH quantities are 0
    zero_qty_mask = (
            (df_tools[TOTAL_QTY_COLUMN] == 0) &
            (df_tools[ALT_QTY_COLUMN] == 0) &
            (df_tools[TOOL_NAME_COLUMN].notna()) &
            (df_tools[TOOL_NAME_COLUMN].astype(str).str.strip() != '') &
            (df_tools[TOOL_PARTNO_COLUMN].notna()) &
            (df_tools[TOOL_PARTNO_COLUMN].astype(str).str.strip() != '')
    )

    zero_qty_items = df_tools[zero_qty_mask].copy()

    if len(zero_qty_items) == 0:
        return pd.DataFrame()

    # Extract Task ID for each row
    zero_qty_items['Task ID'] = zero_qty_items.apply(
        lambda row: extract_task_id_for_tool_control(row, seq_mappings, seq_id_mappings),
        axis=1
    )

    # Map tool type: 'Y' -> 'Tool', 'N' -> 'Spare'
    def map_tool_type(value):
        if pd.isna(value):
            return 'Unknown'
        val_str = str(value).strip().upper()
        if val_str == 'Y':
            return 'Tool'
        elif val_str == 'N':
            return 'Spare'
        else:
            return str(value)

    zero_qty_items['Type'] = zero_qty_items[TOOL_TYPE_COLUMN].apply(map_tool_type)

    # Select and rename columns for output
    result = zero_qty_items[[SEQ_NO_COLUMN, 'Task ID', TOOL_PARTNO_COLUMN,
                             TOOL_NAME_COLUMN, 'Type']].copy()
    result.columns = ['SEQ', 'Task ID', 'Part Number', 'Tool/Spare Name', 'Type']

    # IMPORTANT: NO DEDUPLICATION
    # Each row represents a different part requirement, so we keep ALL rows
    # Even if they have the same SEQ, Task ID, or Part Number

    # Reset index for clean output
    result = result.reset_index(drop=True)

    return result


def process_tool_control(input_file_path, seq_mappings, seq_id_mappings):
    """
    Main function to process tool control independently.

    This function can be called separately and doesn't interfere with
    man-hour calculations or any other processing.

    Args:
        input_file_path: Path to the input Excel file
        seq_mappings: SEQ mapping configuration
        seq_id_mappings: SEQ ID extraction configuration

    Returns:
        DataFrame with tool control issues, or empty DataFrame if none found
    """
    try:
        # Load the uploaded file
        df = pd.read_excel(input_file_path, engine='openpyxl')

        print(f"\nTool Control: Processing {len(df)} total rows from input file...")

        # Check tool availability on ALL rows
        tool_issues = check_tool_availability(df, seq_mappings, seq_id_mappings)

        if len(tool_issues) > 0:
            print(f"Tool Control: Found {len(tool_issues)} tool/spare items with zero availability")

            # Show breakdown by type
            tool_count = len(tool_issues[tool_issues['Type'] == 'Tool'])
            spare_count = len(tool_issues[tool_issues['Type'] == 'Spare'])
            print(f"  - Tools: {tool_count}")
            print(f"  - Spares: {spare_count}")
        else:
            print("Tool Control: All tools/spares have adequate availability")

        return tool_issues

    except Exception as e:
        print(f"ERROR in Tool Control processing: {e}")
        return pd.DataFrame()


def get_tool_control_summary(tool_issues_df):
    """
    Generate a summary of tool control issues.

    Args:
        tool_issues_df: DataFrame with tool control issues

    Returns:
        dict: Summary statistics
    """
    if len(tool_issues_df) == 0:
        return {
            'total_issues': 0,
            'total_tools': 0,
            'total_spares': 0,
            'unique_parts': 0,
            'affected_seqs': 0
        }

    return {
        'total_issues': len(tool_issues_df),
        'total_tools': len(tool_issues_df[tool_issues_df['Type'] == 'Tool']),
        'total_spares': len(tool_issues_df[tool_issues_df['Type'] == 'Spare']),
        'unique_parts': tool_issues_df['Part Number'].nunique(),
        'affected_seqs': tool_issues_df['SEQ'].nunique()
    }