import os
import pandas as pd
from datetime import datetime

# --- Configuration ---
INPUT_DIR = "INPUT"
OUTPUT_DIR = "OUTPUT"
REFERENCE_DIR = "REFERENCE"


def get_reference_b84_value(reference_file_path):
    """
    Extracts the value from cell B84 of the 'List item' sheet in the reference file.
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


def generate_debug_sample(uploaded_file_path, output_txt_path):
    """
    Extracts and logs a sample of 5 random rows from the uploaded file for debugging.
    """
    try:
        # Load the uploaded Excel file
        df = pd.read_excel(uploaded_file_path, engine='openpyxl')

        # Ensure that required columns exist
        required_cols = ["Seq. No.", "Planned Mhrs"]
        if not all(col in df.columns for col in required_cols):
            print(f"   ERROR: File is missing required columns ({required_cols}).")
            return

        # Select a random sample of 5 rows
        sample_size = min(5, len(df))
        random_sample = df.sample(n=sample_size, random_state=1)

        # Log the sample to the debug output
        with open(output_txt_path, "a", encoding="utf-8") as f:
            f.write("\nDEBUG SAMPLE REPORT (Random 5 Rows):\n")
            f.write(f"   Sample Size: {sample_size}\n")
            f.write("   -----------------------------------------------\n")
            f.write("   | Seq. No. | Original Planned Mhrs | Parsed (HH:MM) |\n")
            f.write("   -----------------------------------------------\n")

            for index, row in random_sample.iterrows():
                seq_no = str(row['Seq. No.'])
                original_mhrs = str(row['Planned Mhrs'])
                planned_hours = time_to_hours(row['Planned Mhrs'])
                planned_time_hhmm = hours_to_hhmm(planned_hours)
                f.write(f"   | {seq_no:<8} | {original_mhrs:<21} | {planned_time_hhmm:>12} |\n")

            f.write("   -----------------------------------------------\n")

    except Exception as e:
        print(f"   ERROR generating debug sample: {e}")


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
    Processes files for debugging, focusing on B84 vs C9 comparison and debug sample generation.
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

    # Find ALL Excel files in INPUT/
    excel_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.xlsx')]

    if not excel_files:
        print(f"\nNo .xlsx files found in the '{INPUT_DIR}/' folder.")
        return

    print(f"\nFound {len(excel_files)} file(s) to process.")
    print("=" * 30)

    # Process each Excel file
    for file_name in excel_files:
        file_path = os.path.join(INPUT_DIR, file_name)

        # Generate output file for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder_path = os.path.join(OUTPUT_DIR, file_name.split('.')[0])
        os.makedirs(output_folder_path, exist_ok=True)

        output_txt_path = os.path.join(output_folder_path, f"debug_{timestamp}.txt")

        # Start writing to debug file
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write("--- Debug Report ---\n")
            f.write(f"File: {file_name}\n")
            f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 40 + "\n")

        # Generate debug sample and compare B84 vs C9
        generate_debug_sample(file_path, output_txt_path)
        debug_b84_vs_c9(file_path, reference_b84_value, output_txt_path)

        print(f"   SUCCESS: Debug report saved to {output_txt_path}")


if __name__ == "__main__":
    main()
