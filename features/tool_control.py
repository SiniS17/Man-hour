"""
Tool Control Module - Separate from man-hour calculations
REFACTORED: Now uses centralized logging system
"""

import pandas as pd
import os
from utils.logger import get_logger
from core.config import (SEQ_NO_COLUMN, TITLE_COLUMN,
                         TOOL_NAME_COLUMN, TOOL_TYPE_COLUMN, TOOL_PARTNO_COLUMN,
                         TOTAL_QTY_COLUMN, ALT_QTY_COLUMN, config)

# Get module-specific logger
logger = get_logger(module_name="tool_control")


def load_ignore_items():
    """
    Load items to ignore from ignore_item.txt file.

    Returns:
        set: Set of items (lowercase) to ignore
    """
    reference_folder = config.get('Paths', 'reference_folder', fallback='REFERENCE')
    ignore_file = os.path.join(reference_folder, 'ignore_item.txt')

    ignore_items = set()

    if not os.path.exists(ignore_file):
        logger.info(f"ignore_item.txt not found at {ignore_file}")
        logger.info("No items will be ignored during tool control checking")
        return ignore_items

    try:
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                item = line.strip()

                # Skip empty lines and comments
                if not item or item.startswith('#'):
                    continue

                # Add lowercase version for case-insensitive matching
                ignore_items.add(item.lower())

        if ignore_items:
            logger.info(f"Loaded {len(ignore_items)} items to ignore from ignore_item.txt")
        else:
            logger.info("ignore_item.txt is empty, no items will be ignored")

    except Exception as e:
        logger.warning(f"Could not load ignore_item.txt: {e}")
        logger.warning("Proceeding without ignore list")

    return ignore_items


def should_ignore_item(part_number, tool_name, ignore_items):
    """
    Check if an item should be ignored based on the ignore list.

    Args:
        part_number: Part number string
        tool_name: Tool/spare name string
        ignore_items: Set of items to ignore (lowercase)

    Returns:
        tuple: (should_ignore: bool, reason: str)
    """
    if not ignore_items:
        return False, ""

    # Check part number
    if pd.notna(part_number):
        part_str = str(part_number).strip().lower()
        if part_str in ignore_items:
            return True, f"part number '{part_number}' in ignore list"

    # Check tool/spare name
    if pd.notna(tool_name):
        name_str = str(tool_name).strip().lower()
        if name_str in ignore_items:
            return True, f"tool name '{tool_name}' in ignore list"

    return False, ""


def extract_task_id_for_tool_control(row, seq_mappings, seq_id_mappings):
    """
    Extract Task ID for tool control purposes.

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
        if "(" in title:
            return title.split("(")[0].strip()
        return title.strip()
    elif id_extraction_method == "/":
        if "/" in title:
            return title.split("/")[0].strip()
        return title.strip()
    else:
        return title.strip()


def check_tool_availability(df, seq_mappings, seq_id_mappings):
    """
    Check for tools/spares with zero quantity.
    Filters out items that are in the ignore list.

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
        logger.warning("Tool control columns not properly configured in settings.ini")
        return pd.DataFrame()

    required_tool_cols = [TOOL_NAME_COLUMN, TOOL_TYPE_COLUMN, TOOL_PARTNO_COLUMN,
                          TOTAL_QTY_COLUMN, ALT_QTY_COLUMN]
    missing_cols = [col for col in required_tool_cols if col not in df.columns]

    if missing_cols:
        logger.warning(f"Tool control columns not found in file: {missing_cols}")
        return pd.DataFrame()

    # Load ignore list
    ignore_items = load_ignore_items()

    # Create a working copy
    df_tools = df.copy()

    # Convert quantity columns to numeric
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

    logger.info(f"Found {len(zero_qty_items)} items with zero availability (before filtering)")

    # Apply ignore list filtering
    filtered_items = []
    ignored_count = 0

    for idx, row in zero_qty_items.iterrows():
        part_number = row[TOOL_PARTNO_COLUMN]
        tool_name = row[TOOL_NAME_COLUMN]

        should_ignore, reason = should_ignore_item(part_number, tool_name, ignore_items)

        if should_ignore:
            ignored_count += 1
            if ignored_count <= 5:
                logger.debug(f"Ignoring: {part_number} - {tool_name} ({reason})")
        else:
            filtered_items.append(row)

    if ignored_count > 0:
        logger.info(f"Ignored {ignored_count} items from ignore_item.txt")
        if ignored_count > 5:
            logger.debug(f"(showing first 5, {ignored_count - 5} more ignored)")

    # Convert filtered list back to DataFrame
    if not filtered_items:
        logger.info("All items with zero availability are in ignore list")
        return pd.DataFrame()

    zero_qty_items = pd.DataFrame(filtered_items)

    # Extract Task ID for each row
    zero_qty_items['Task ID'] = zero_qty_items.apply(
        lambda row: extract_task_id_for_tool_control(row, seq_mappings, seq_id_mappings),
        axis=1
    )

    # Map tool type
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

    # Select and rename columns
    result = zero_qty_items[[SEQ_NO_COLUMN, 'Task ID', TOOL_PARTNO_COLUMN,
                             TOOL_NAME_COLUMN, 'Type']].copy()
    result.columns = ['SEQ', 'Task ID', 'Part Number', 'Tool/Spare Name', 'Type']

    # Reset index
    result = result.reset_index(drop=True)

    return result


def process_tool_control(input_file_path, seq_mappings, seq_id_mappings):
    """
    Main function to process tool control independently.

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

        logger.info(f"Processing {len(df)} total rows from input file...")

        # Check tool availability
        tool_issues = check_tool_availability(df, seq_mappings, seq_id_mappings)

        if len(tool_issues) > 0:
            logger.info(f"Found {len(tool_issues)} tool/spare items requiring attention")

            # Show breakdown by type
            tool_count = len(tool_issues[tool_issues['Type'] == 'Tool'])
            spare_count = len(tool_issues[tool_issues['Type'] == 'Spare'])
            logger.info(f"  - Tools: {tool_count}")
            logger.info(f"  - Spares: {spare_count}")
        else:
            logger.info("All tools/spares either have adequate availability or are in ignore list")

        return tool_issues

    except Exception as e:
        logger.error(f"Error in Tool Control processing: {e}")
        import traceback
        logger.debug(traceback.format_exc())
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