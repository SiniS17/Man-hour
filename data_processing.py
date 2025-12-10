import pandas as pd
from config import SEQ_NO_COLUMN, TITLE_COLUMN, WORK_STEP_COLUMN, PLANNED_MHRS_COLUMN, HIGH_MHRS_HOURS, \
    RANDOM_SAMPLE_SIZE, SEQ_ID_MAPPINGS


def extract_task_id(row):
    """
    Extracts the task ID based on the 'Seq. No.' and dynamically mapped columns (Title, Work Step, or Ignore).
    Returns a tuple: (task_id, should_check_reference)
    """
    seq_no = str(row[SEQ_NO_COLUMN])

    # Extract the SEQ prefix (e.g., "4.39" -> "4")
    seq_prefix = seq_no.split('.')[0]

    # Get the corresponding column or action from SEQ_ID_MAPPINGS
    # Use uppercase to match the config parser (which lowercases keys by default, but we convert to uppercase)
    mapping_key = f"SEQ_{seq_prefix}.X_ID"
    seq_id_mapping = SEQ_ID_MAPPINGS.get(mapping_key, "default")

    # Debug: print the mapping lookup
    # print(f"DEBUG: Seq {seq_no} -> Key: {mapping_key} -> Mapping: {seq_id_mapping}")

    if seq_id_mapping == "work_step" or seq_id_mapping == "default":
        task_id = str(row[WORK_STEP_COLUMN])
        return (task_id, True)  # Should check against reference

    elif seq_id_mapping == "title":
        title = str(row[TITLE_COLUMN])
        # Extract task ID before the first '/' and remove "-R00" suffix
        task_id = title.split('/')[0].strip().replace("-R00", "")
        return (task_id, True)  # Should check against reference

    elif seq_id_mapping == "ignore":
        # Still parse the work_step, but mark it as "should not check"
        task_id = str(row[WORK_STEP_COLUMN])
        print(f"Ignoring task ID for Seq. No: {seq_no} (using work_step): {task_id}")
        return (task_id, False)  # Should NOT check against reference

    return (None, False)


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


def process_data(input_file_path, reference_ids):
    """
    Main data processing function. This will extract task IDs, validate man-hours, and generate a report.
    """
    # Load the uploaded file
    df = pd.read_excel(input_file_path, engine='openpyxl')

    # Ensure necessary columns are present
    required_columns = [SEQ_NO_COLUMN, TITLE_COLUMN, WORK_STEP_COLUMN, PLANNED_MHRS_COLUMN]
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns in the uploaded file. Expected: {required_columns}")

    # Convert "Planned Mhrs" to total hours
    df['Planned Hours'] = df[PLANNED_MHRS_COLUMN].apply(convert_planned_mhrs)

    # Extract task IDs and check flags
    task_id_data = df.apply(extract_task_id, axis=1)
    df['Task ID'] = task_id_data.apply(lambda x: x[0])
    df['Should Check Reference'] = task_id_data.apply(lambda x: x[1])

    # Debugging: Print rows with None task IDs
    none_task_ids = df[df['Task ID'].isna()]
    if not none_task_ids.empty:
        print(f"Rows with None Task IDs (Seq. No. and respective rows):")
        print(none_task_ids[[SEQ_NO_COLUMN, TITLE_COLUMN, WORK_STEP_COLUMN, 'Task ID']])

    # Identify high man-hours tasks
    high_mhrs_tasks = df[df['Planned Hours'] > HIGH_MHRS_HOURS]

    # Check for new task IDs (only for rows that should be checked)
    # Filter to only check rows where 'Should Check Reference' is True
    rows_to_check = df[df['Should Check Reference'] == True]
    new_task_ids = rows_to_check[~rows_to_check['Task ID'].isin(reference_ids)]['Task ID'].unique()

    # Generate a random sample for debugging
    sample_size = min(RANDOM_SAMPLE_SIZE, len(df))
    random_sample = df.sample(n=sample_size, random_state=1)

    # Create the report
    report = generate_report(df, high_mhrs_tasks, random_sample, new_task_ids)

    return report


def generate_report(df, high_mhrs_tasks, random_sample, new_task_ids):
    """
    Generate the formatted report with total hours, high Mhrs tasks, random sample, and new task IDs.
    """
    report = []

    # Total planned man-hours
    total_mhrs = df['Planned Hours'].sum()
    report.append(f"Total Planned Man-Hours: {total_mhrs:.2f} hours")

    # High man-hours tasks
    report.append("\n2. Tasks with Planned Mhrs > 16 hours:")
    report.append(f"Found {len(high_mhrs_tasks)} tasks.")
    report.append("--------------------------------------------------")
    report.append("| Seq. No. | Planned Mhrs (HH:MM) |")
    report.append("--------------------------------------------------")

    for index, row in high_mhrs_tasks.iterrows():
        seq_no = str(row[SEQ_NO_COLUMN])
        planned_hours = row['Planned Hours']
        planned_time_hhmm = hours_to_hhmm(planned_hours)
        report.append(f"| {seq_no:<8} | {planned_time_hhmm:>18} |")
    report.append("--------------------------------------------------")

    # Random sample report
    report.append("\n3. DEBUG SAMPLE REPORT (Random 10 Rows):")
    report.append("| Seq. No. | Title                          | Task ID          | Check? | Planned Mhrs |")
    report.append("-------------------------------------------------------------------------------------------")
    for index, row in random_sample.iterrows():
        seq_no = str(row[SEQ_NO_COLUMN])
        title = str(row[TITLE_COLUMN])[:30]  # Truncate title
        task_id = str(row['Task ID'])[:16]  # Truncate task ID
        should_check = "Yes" if row['Should Check Reference'] else "No"
        planned_hours = row['Planned Hours']
        planned_time_hhmm = hours_to_hhmm(planned_hours)
        report.append(f"| {seq_no:<8} | {title:<30} | {task_id:<16} | {should_check:<6} | {planned_time_hhmm:>12} |")
    report.append("-------------------------------------------------------------------------------------------")

    # New Task IDs
    if len(new_task_ids) > 0:
        report.append(f"\n4. New Task IDs (not in reference): {len(new_task_ids)} found")
        report.append("--------------------------------------------------")
        for task_id in new_task_ids:
            if task_id and task_id != 'nan':  # Filter out None and 'nan' values
                report.append(f"   - {task_id}")
        report.append("--------------------------------------------------")
    else:
        report.append("\n4. New Task IDs: None found (all task IDs match reference)")

    return "\n".join(report)


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