import pandas as pd
from config import SEQ_NO_COLUMN, TITLE_COLUMN, WORK_STEP_COLUMN, PLANNED_MHRS_COLUMN, HIGH_MHRS_HOURS, RANDOM_SAMPLE_SIZE, SEQ_ID_MAPPINGS

def extract_task_id(row):
    """
    Extracts the task ID based on the 'Seq. No.' and dynamically mapped columns (Title, Work Step, or Ignore).
    """
    seq_no = str(row[SEQ_NO_COLUMN])

    # Get the corresponding column or action from SEQ_ID_MAPPINGS
    seq_id_mapping = SEQ_ID_MAPPINGS.get(f"SEQ_{seq_no.split('.')[0]}.x_ID", "default")  # Default to 'work_step'

    if seq_id_mapping == "work_step" or seq_id_mapping == "default":
        return str(row[WORK_STEP_COLUMN])  # Use work_step as default for task ID
    elif seq_id_mapping == "title":
        title = str(row[TITLE_COLUMN])
        return title.split('/')[0].replace("-R00", "")  # Extract task ID before the first '/'
    elif seq_id_mapping == "ignore":
        # Log ignored task IDs (still parse, but don't check against reference)
        print(f"Ignoring task ID for Seq. No: {seq_no} (using work_step): {str(row[WORK_STEP_COLUMN])}")
        return str(row[WORK_STEP_COLUMN])  # Still parse the ID, but don't check it
    return None

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
            hours, minutes = map(int, time_str.split(':')[:2])
            seconds = int(time_str.split(':')[2]) if len(time_str.split(':')) == 3 else 0
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

    # Extract task IDs
    df['Task ID'] = df.apply(extract_task_id, axis=1)

    # Debugging: Print rows with None task IDs
    none_task_ids = df[df['Task ID'].isna()]
    if not none_task_ids.empty:
        print(f"Rows with None Task IDs (Seq. No. and respective rows):")
        print(none_task_ids[[SEQ_NO_COLUMN, TITLE_COLUMN, WORK_STEP_COLUMN, 'Task ID']])

    # Identify high man-hours tasks
    high_mhrs_tasks = df[df['Planned Hours'] > HIGH_MHRS_HOURS]

    # Check for new task IDs (those not found in the reference)
    new_task_ids = df[~df['Task ID'].isin(reference_ids)]['Task ID'].unique()

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
    report.append("\n3. DEBUG SAMPLE REPORT (Random 5 Rows):")
    for index, row in random_sample.iterrows():
        seq_no = str(row[SEQ_NO_COLUMN])
        title = str(row[TITLE_COLUMN])
        planned_hours = row['Planned Hours']
        planned_time_hhmm = hours_to_hhmm(planned_hours)
        report.append(f"| {seq_no:<8} | {title:<30} | {planned_time_hhmm:>12} |")
    report.append("--------------------------------------------------")

    # New Task IDs
    if len(new_task_ids) > 0:
        report.append("\nNew Task IDs:")
        for task_id in new_task_ids:
            report.append(task_id)

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
