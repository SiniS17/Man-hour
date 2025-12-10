import glob
import os
import pandas as pd
from datetime import datetime, timedelta

# --- Configuration ---
INPUT_DIR = "INPUT"
OUTPUT_DIR = "OUTPUT"
REFERENCE_DIR = "REFERENCE"


def get_reference_ids(reference_file_path):
    """
    Loads the 'B787 list task' file and extracts the 'J0BCARD' IDs from the 'List item' sheet.
    """
    try:
        # Load the reference file
        ref_df = pd.read_excel(reference_file_path, sheet_name='List item', engine='openpyxl')

        # Print the first 100 rows of the 'J0BCARD' column for debugging
        print(f"First 100 rows of 'J0BCARD' column:\n{ref_df['J0BCARD'].head(100)}")

        # Clean the 'J0BCARD' column by stripping spaces and ensuring no blank values
        reference_ids = ref_df['J0BCARD'].dropna().apply(str).str.strip().unique()

        return set(reference_ids)  # Return as a set to ensure uniqueness

    except Exception as e:
        print(f"   ERROR reading reference file for J0BCARD: {e}")
        return set()





def extract_task_id(row):
    """
    Extracts the task ID based on the 'Seq. No.' and 'Title' fields.
    """
    seq_no = str(row['Seq. No.'])
    if seq_no.startswith("3."):
        return str(row['Work Step / Event Number'])
    elif seq_no.startswith("4."):
        title = str(row['Title'])
        # Extract ID before the first "/"
        return title.split('/')[0].replace("-R00", "")
    return None


def check_task_ids(uploaded_file_path, reference_ids, output_txt_path):
    """
    Compares the task IDs in the uploaded file against the reference IDs.
    Identifies new tasks and writes the new task IDs to the output file.
    """
    try:
        # Load the uploaded file
        df = pd.read_excel(uploaded_file_path, engine='openpyxl')

        new_task_ids = []
        # Loop through each row in the uploaded file
        for _, row in df.iterrows():
            task_id = extract_task_id(row)
            if task_id:
                # Stripping whitespace and converting to uppercase for comparison
                task_id = task_id.strip().upper()

                # Compare the task ID against every reference ID in the same way
                matching_ids = [str(ref_id.strip().upper()) for ref_id in reference_ids]

                # Check if the task ID is found in the reference list
                if task_id not in matching_ids:
                    new_task_ids.append(task_id)

        # Output new task IDs to console
        if new_task_ids:
            print(f"New Task IDs: {new_task_ids}")
        else:
            print("No new task IDs found.")

        # Write new task IDs to the output file
        if new_task_ids:
            with open(output_txt_path, "a", encoding="utf-8") as f:
                f.write("\nNew Task IDs:\n")
                f.write("\n".join(new_task_ids))
                f.write("\n")

    except Exception as e:
        print(f"   ERROR processing uploaded file: {e}")



def get_reference_b84_value(reference_file_path):
    """
    Extracts the value from cell B84 of the 'List item' sheet in the 'B787 list task' reference file.
    """
    try:
        reference_df = pd.read_excel(reference_file_path, sheet_name='List item', engine='openpyxl')
        b84_value = reference_df.at[83, 'J0BCARD']  # Adjusted to 'J0BCARD' column based on your preview
        return str(b84_value).strip()  # Return the value as a string, stripped of extra spaces
    except Exception as e:
        print(f"   ERROR reading reference file for B84: {e}")
        return None


def extract_c9_value(uploaded_file_path):
    """
    Extracts the value from cell C9 of the uploaded file.
    """
    try:
        uploaded_df = pd.read_excel(uploaded_file_path, engine='openpyxl', header=None)
        c9_value = str(uploaded_df.at[8, 2]).strip()  # C9 is at row 8, column 2 (zero-indexed)
        return c9_value
    except Exception as e:
        print(f"   ERROR reading uploaded file for C9: {e}")
        return None


def debug_b84_vs_c9(uploaded_file_path, reference_b84_value, output_txt_path):
    """
    Compares B84 from the reference file and C9 from the uploaded file.
    Logs the result in the output text file.
    """
    try:
        # Extract value from C9 of the uploaded file
        c9_value = extract_c9_value(uploaded_file_path)

        if c9_value:
            # Write the comparison result to the output file
            with open(output_txt_path, "a", encoding="utf-8") as f:
                f.write("\nB84 vs C9 Comparison:\n")
                f.write(f"   B84 (Reference): {reference_b84_value}\n")
                f.write(f"   C9 (Uploaded): {c9_value}\n")

                if reference_b84_value == c9_value:
                    f.write("   The values are identical.\n")
                else:
                    f.write("   The values are different.\n")
        else:
            print("   C9 value not found in the uploaded file.")

    except Exception as e:
        print(f"   ERROR in B84 vs C9 comparison: {e}")


def process_excel_file(input_file_path, reference_b84_value, reference_ids):
    """
    Reads an Excel file, processes the task data, and compares B84 vs C9.
    """
    base_filename = os.path.basename(input_file_path)
    file_name_no_ext = os.path.splitext(base_filename)[0]

    print(f"-> Processing: {base_filename}")

    # 1. Read the Excel file using pandas
    try:
        df = pd.read_excel(input_file_path, engine='openpyxl')
    except Exception as e:
        print(f"   ERROR reading file: {e}")
        return

    # Check for required columns
    required_cols = ["Planned Mhrs", "Seq. No."]
    if not all(col in df.columns for col in required_cols):
        print(f"   ERROR: File is missing required columns ({required_cols}). Skipping.")
        return

    # 2. Convert "Planned Mhrs" to float hours
    df['Planned Hours'] = df['Planned Mhrs'].apply(time_to_hours)

    clean_df = df.dropna(how='all')

    # 3. Prepare output folder and file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder_path = os.path.join(OUTPUT_DIR, file_name_no_ext)
    os.makedirs(output_folder_path, exist_ok=True)

    txt_filename = f"{file_name_no_ext}_Report_{timestamp}.txt"
    output_txt_path = os.path.join(output_folder_path, txt_filename)

    # Write initial content to the TXT report
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("--- Man-Hour Processing Report ---\n")
        f.write(f"Input File: {base_filename}\n")
        f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 40 + "\n")

        # Section 1: Total (Kept as decimal hours for aggregation clarity)
        total_mhrs = clean_df['Planned Hours'].sum()
        f.write("1. Total Planned Man-Hours:\n")
        f.write(f"   Total Planned Mhrs: {total_mhrs:.2f} hours\n")
        f.write("-" * 40 + "\n")

        # Section 2: High Mhrs Tasks
        high_mhr_tasks = clean_df[clean_df['Planned Hours'] > 16]
        f.write("2. Tasks with Planned Mhrs > 16 hours:\n")

        if not high_mhr_tasks.empty:
            f.write(f"   Found {len(high_mhr_tasks)} tasks.\n")
            f.write("   -----------------------------------\n")
            f.write("   | Seq. No. | Planned Mhrs (HH:MM) |\n")
            f.write("   -----------------------------------\n")

            for index, row in high_mhr_tasks.iterrows():
                seq_no = str(row['Seq. No.'])
                planned_hours = row['Planned Hours']
                planned_time_hhmm = hours_to_hhmm(planned_hours)
                f.write(f"   | {seq_no:<8} | {planned_time_hhmm:>18} |\n")

            f.write("   -----------------------------------\n")
        else:
            f.write("   No tasks found with Planned Mhrs > 16 hours.\n")

        f.write("-" * 40 + "\n")

        # Section 3: Debug Sample Report
        f.write("3. DEBUG SAMPLE REPORT (5 Random Rows):\n")
        sample_size = min(5, len(clean_df))
        f.write(f"   Sample Size: {sample_size}\n")
        f.write("   --------------------------------------------------\n")
        f.write("   | Seq. No. | Original Planned Mhrs | Parsed (HH:MM)|\n")
        f.write("   --------------------------------------------------\n")

        if not clean_df.empty:
            random_sample = clean_df.sample(n=sample_size, random_state=1)
            for index, row in random_sample.iterrows():
                seq_no = str(row['Seq. No.'])
                original_mhrs = str(row['Planned Mhrs'])
                parsed_hours = row['Planned Hours']
                parsed_time_hhmm = hours_to_hhmm(parsed_hours)
                f.write(f"   | {seq_no:<8} | {original_mhrs:<21} | {parsed_time_hhmm:>12} |\n")
        else:
            f.write("   No rows available to sample.\n")

        f.write("   --------------------------------------------------\n")

    # Perform the B84 vs C9 comparison and log the result in the output file
    debug_b84_vs_c9(input_file_path, reference_b84_value, output_txt_path)

    # Check and write new task IDs
    check_task_ids(input_file_path, reference_ids, output_txt_path)

    print(f"   SUCCESS: Report saved to {output_txt_path}")


def time_to_hours(time_val):
    """
    Converts Excel time values (which may include days, e.g., '1 day 12:30:00')
    into a float representing total hours.
    """
    if pd.isna(time_val):
        return 0.0

    if isinstance(time_val, timedelta):
        return time_val.total_seconds() / 3600.0

    if isinstance(time_val, (float, int)):
        if 0 < time_val < 1:
            return time_val * 24.0
        else:
            return float(time_val)

    try:
        time_str = str(time_val).strip()
        if time_str.count(':') >= 1:
            return pd.to_timedelta(time_str).total_seconds() / 3600.0
    except Exception:
        pass

    return 0.0


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


def main():
    """
    Initializes directories and processes all Excel files found in the INPUT folder.
    """
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Reference file path
    reference_file_path = os.path.join(os.getcwd(), REFERENCE_DIR, "B787 list task.xlsx")

    # Load reference B84 value
    reference_b84_value = get_reference_b84_value(reference_file_path)
    if reference_b84_value is None:
        print("   ERROR: B84 value could not be loaded from the reference file.")
        return

    # Load reference IDs
    reference_ids = get_reference_ids(reference_file_path)

    # Find ALL Excel files in INPUT/
    excel_files = glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))

    if not excel_files:
        print(f"\nNo .xlsx files found in the '{INPUT_DIR}/' folder.")
        print("Please place your Excel files there and run the script again.")
        return

    print(f"\nFound {len(excel_files)} file(s) to process.")
    print("=" * 30)

    for file_path in excel_files:
        process_excel_file(file_path, reference_b84_value, reference_ids)

    print("=" * 30)
    print("All files processed successfully.")


if __name__ == "__main__":
    main()
