"""
ID Extractor Module
Handles extraction of task IDs from titles based on SEQ configuration
"""

from .config import SEQ_NO_COLUMN, TITLE_COLUMN, SEQ_MAPPINGS, SEQ_ID_MAPPINGS


def extract_task_id(row):
    """
    Extracts the task ID based on the 'Seq. No.' and dynamically mapped columns.

    Args:
        row: DataFrame row

    Returns:
        tuple: (task_id, should_check_reference, should_process)
            - task_id: The extracted ID
            - should_check_reference: Whether to check against reference for new IDs
            - should_process: Whether to include this row in processing at all
    """
    seq_no = str(row[SEQ_NO_COLUMN])

    # Extract the SEQ prefix (e.g., "4.39" -> "4")
    seq_prefix = seq_no.split('.')[0]

    # Get the processing mode from SEQ_MAPPINGS
    mapping_key = f"SEQ_{seq_prefix}.X"
    seq_mapping = SEQ_MAPPINGS.get(mapping_key, "true")

    # If set to "ignore", skip this row entirely
    if seq_mapping == "ignore":
        return (None, False, False)  # Don't process at all

    # Get the ID extraction method from SEQ_ID_MAPPINGS
    id_mapping_key = f"SEQ_{seq_prefix}.X_ID"
    id_extraction_method = SEQ_ID_MAPPINGS.get(id_mapping_key, "/")

    # Extract the task ID from the title
    title = str(row[TITLE_COLUMN])
    task_id = extract_id_from_title(title, id_extraction_method)

    # Determine if we should check reference based on SEQ_MAPPINGS value
    should_check = (seq_mapping == "true")

    return (task_id, should_check, True)  # Process this row


def extract_id_from_title(title, extraction_method):
    """
    Extracts the ID from the title based on the extraction method.

    Args:
        title (str): The title string
        extraction_method (str): Either "-" or "/"

    Returns:
        str: The extracted ID string

    Examples:
        >>> extract_id_from_title("24-045-00 (00) - ITEM 1", "-")
        '24-045-00'
        >>> extract_id_from_title("EO-2024-001 / CABIN AIR SYSTEM", "/")
        'EO-2024-001'
    """
    if extraction_method == "-":
        # Extract everything before "(" (e.g., "24-045-00 (00) - ITEM 1" -> "24-045-00")
        if "(" in title:
            id_part = title.split("(")[0].strip()
            return id_part
        else:
            return title.strip()

    elif extraction_method == "/":
        # Extract everything before the first "/"
        if "/" in title:
            return title.split("/")[0].strip()
        else:
            return title.strip()

    else:
        # Default: return the whole title
        return title.strip()


def get_seq_prefix(seq_no):
    """
    Extract the major version prefix from a SEQ number.

    Args:
        seq_no: SEQ identifier (e.g., "2.1", "3.5", "4.2")

    Returns:
        str: The major version (e.g., "2", "3", "4")

    Examples:
        >>> get_seq_prefix("2.1")
        '2'
        >>> get_seq_prefix("3.45")
        '3'
    """
    return str(seq_no).split('.')[0]


def should_process_seq(seq_no):
    """
    Determine if a SEQ should be processed based on configuration.

    Args:
        seq_no: SEQ identifier

    Returns:
        bool: True if SEQ should be processed, False if it should be ignored
    """
    seq_prefix = get_seq_prefix(seq_no)
    mapping_key = f"SEQ_{seq_prefix}.X"
    seq_mapping = SEQ_MAPPINGS.get(mapping_key, "true")

    return seq_mapping != "ignore"


def should_check_reference(seq_no):
    """
    Determine if a SEQ's task IDs should be checked against reference.

    Args:
        seq_no: SEQ identifier

    Returns:
        bool: True if should check reference, False otherwise
    """
    seq_prefix = get_seq_prefix(seq_no)
    mapping_key = f"SEQ_{seq_prefix}.X"
    seq_mapping = SEQ_MAPPINGS.get(mapping_key, "true")

    return seq_mapping == "true"