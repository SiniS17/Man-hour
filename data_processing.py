import pandas as pd
import re

# Import all required configs
from config import (SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN,
                    HIGH_MHRS_HOURS, RANDOM_SAMPLE_SIZE, SEQ_MAPPINGS, SEQ_ID_MAPPINGS,
                    ENABLE_SPECIAL_CODE, SPECIAL_CODE_COLUMN)


def extract_task_id(row):
    """
    Extracts the task ID based on the 'Seq. No.' and dynamically mapped columns.
    Returns a tuple: (task_id, should_check_reference, should_process)
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
        title: The title string
        extraction_method: Either "-" or "/"

    Returns:
        The extracted ID string
    """
    if extraction_method == "-":
        # Extract everything before "-" and remove any "(00)" pattern
        if "-" in title:
            id_part = title.split("-")[0].strip()
            # Remove (00) pattern if present
            id_part = re.sub(r'\s*\(\d+\)\s*', '', id_part)
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


def convert_planned_mhrs(time_val):
    """
    Converts Excel time values (which may include days, e.g., '1 day 12:30:00')
    into a float representing total hours.
    """
    if pd.isna(time_val):
        return 0.0

    if isinstance(time_val, (int, float)):
        # Handle as raw numeric hours if it's already in hours format
        return float(time_val)

    try:
        time_str = str(time_val).strip()

        # Check if time includes days
        if 'day' in time_str:
            # Example: '1 day 12:30:00' or '0 days 00:00:00'
            days_part, time_part = time_str.split(' days ')
            hours, minutes, seconds = map(int, time_part.split(':'))
            total_hours = int(days_part) * 24 + hours + minutes / 60 + seconds / 3600
            return total_hours
        elif ':' in time_str:
            # Example: '12:30' or '12:30:00'
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            seconds = int(parts[2]) if len(parts) > 2 else 0
            return hours + minutes / 60 + seconds / 3600

    except Exception as e:
        print(f"Error converting time: {e}")
    return 0.0


def calculate_special_code_distribution(df):
    """
    Calculate the distribution of planned hours by special code.
    Returns a sorted dictionary of {special_code: total_hours}
    """
    # Group by special code and sum the planned hours
    special_code_groups = df.groupby(SPECIAL_CODE_COLUMN)['Planned Hours'].sum()

    # Sort by hours (descending) and convert to dictionary
    special_code_dict = special_code_groups.sort_values(ascending=False).to_dict()

    return special_code_dict


def process_data(input_file_path, reference_ids):
    """
    Main data processing function. This will extract task IDs, validate man-hours, and generate a report.
    Returns a dictionary with structured data for Excel output.
    """
    # Load the uploaded file
    df = pd.read_excel(input_file_path, engine='openpyxl')

    # Build list of required columns based on configuration
    required_columns = [SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN]

    # Add special code column to required list if enabled and configured
    if ENABLE_SPECIAL_CODE:
        if SPECIAL_CODE_COLUMN is None:
            print(f"WARNING: Special code is enabled but 'special_code' column is not configured in settings.ini.")
            print("Proceeding without special code analysis...")
            enable_special_code_processing = False
        elif SPECIAL_CODE_COLUMN not in df.columns:
            print(f"WARNING: Special code is enabled but column '{SPECIAL_CODE_COLUMN}' not found in file.")
            print("Proceeding without special code analysis...")
            enable_special_code_processing = False
        else:
            required_columns.append(SPECIAL_CODE_COLUMN)
            enable_special_code_processing = True
    else:
        enable_special_code_processing = False

    # Check for required columns (excluding special code if not found)
    base_required = [SEQ_NO_COLUMN, TITLE_COLUMN, PLANNED_MHRS_COLUMN]
    if not all(col in df.columns for col in base_required):
        raise ValueError(f"Missing required columns in the uploaded file. Expected: {base_required}")

    # Convert "Planned Mhrs" to total hours
    df['Planned Hours'] = df[PLANNED_MHRS_COLUMN].apply(convert_planned_mhrs)

    # Extract task IDs and check flags
    task_id_data = df.apply(extract_task_id, axis=1)
    df['Task ID'] = task_id_data.apply(lambda x: x[0])
    df['Should Check Reference'] = task_id_data.apply(lambda x: x[1])
    df['Should Process'] = task_id_data.apply(lambda x: x[2])

    # Filter out rows that should not be processed (ignore mode)
    df_processed = df[df['Should Process'] == True].copy()

    print(f"Total rows: {len(df)}")
    print(f"Rows to process: {len(df_processed)}")
    print(f"Rows ignored: {len(df) - len(df_processed)}")

    # Debugging: Print rows with None task IDs
    none_task_ids = df_processed[df_processed['Task ID'].isna()]
    if not none_task_ids.empty:
        print(f"Rows with None Task IDs (Seq. No. and respective rows):")
        print(none_task_ids[[SEQ_NO_COLUMN, TITLE_COLUMN, 'Task ID']])

    # Identify high man-hours tasks (only from processed rows)
    high_mhrs_tasks = df_processed[df_processed['Planned Hours'] > HIGH_MHRS_HOURS]

    # Check for new task IDs (only for rows that should be checked)
    rows_to_check = df_processed[df_processed['Should Check Reference'] == True]
    new_task_ids = rows_to_check[~rows_to_check['Task ID'].isin(reference_ids)]['Task ID'].unique()

    # Generate a random sample for debugging (only from processed rows)
    sample_size = min(RANDOM_SAMPLE_SIZE, len(df_processed))
    random_sample = df_processed.sample(n=sample_size, random_state=1) if len(df_processed) > 0 else pd.DataFrame()

    # Calculate special code distribution if enabled (only from processed rows)
    special_code_distribution = None
    if enable_special_code_processing:
        special_code_distribution = calculate_special_code_distribution(df_processed)

    # Calculate total man-hours (only from processed rows)
    total_mhrs = df_processed['Planned Hours'].sum()

    # Return structured data dictionary matching input_output.py expectations
    return {
        'total_mhrs': total_mhrs,
        'total_mhrs_hhmm': hours_to_hhmm(total_mhrs),
        'special_code_distribution': special_code_distribution,
        'enable_special_code': enable_special_code_processing,
        'high_mhrs_tasks': high_mhrs_tasks,
        'new_task_ids': new_task_ids,
        'debug_sample': random_sample,
        'high_mhrs_threshold': HIGH_MHRS_HOURS
    }


def hours_to_hhmm(hours):
    """
    Converts a float representing total hours (e.g., 36.5) into an HH:MM string (e.g., "36:30").
    """
    if hours < 0:
        return "00:00"

    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60

    return f"{h:02d}:{m:02d}"