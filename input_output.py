import os
import pandas as pd
import glob
from datetime import datetime
from config import INPUT_FOLDER, OUTPUT_FOLDER, SEQ_NO_COLUMN, TITLE_COLUMN


# Load all Excel files from the input folder
def load_input_files():
    input_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))
    if not input_files:
        print(f"No .xlsx files found in the '{INPUT_FOLDER}' folder.")
    return input_files


# Save the processed data to an Excel output file and debug log
def save_output_file(input_file_name, report_data):
    """
    Save the report data to Excel file and debug log.

    Args:
        input_file_name: Name of the input file
        report_data: Dictionary containing:
            - 'total_mhrs': float (adjusted with coefficients)
            - 'total_base_mhrs': float (before coefficients)
            - 'total_mhrs_hhmm': str
            - 'total_base_mhrs_hhmm': str
            - 'special_code_distribution': dict or None
            - 'special_code_per_day': dict or None
            - 'workpack_days': int or None
            - 'start_date': datetime or None
            - 'end_date': datetime or None
            - 'enable_special_code': bool
            - 'high_mhrs_tasks': DataFrame
            - 'new_task_ids_with_seq': DataFrame
            - 'debug_sample': DataFrame
            - 'high_mhrs_threshold': int
    """
    # Create a subfolder for each input file in OUTPUT
    base_filename = os.path.splitext(os.path.basename(input_file_name))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(OUTPUT_FOLDER, base_filename)
    os.makedirs(output_folder, exist_ok=True)

    # Define output Excel file path
    output_xlsx_path = os.path.join(output_folder, f"{base_filename}_{timestamp}.xlsx")

    # Create Excel writer
    with pd.ExcelWriter(output_xlsx_path, engine='openpyxl') as writer:
        # Sheet 1: Total Man-Hours
        create_total_mhrs_sheet(writer, report_data)

        # Sheet 2: High Man-Hours Tasks
        create_high_mhrs_sheet(writer, report_data)

        # Sheet 3: New Task IDs
        create_new_task_ids_sheet(writer, report_data)

        # Sheet 4: Tool Control (if enabled)
        if report_data.get('enable_tool_control', False):
            create_tool_control_sheet(writer, report_data)

    print(f"Excel report saved to {output_xlsx_path}")

    # Save debug log to LOG folder in root directory
    save_debug_log(base_filename, timestamp, report_data)


def create_total_mhrs_sheet(writer, report_data):
    """Create the Total Man-Hours sheet with Special Code distribution and average per day"""
    data = []

    total_hours = report_data['total_mhrs']
    total_base_hours = report_data.get('total_base_mhrs', total_hours)
    total_time_str = hours_to_hhmm(total_hours)
    total_base_time_str = hours_to_hhmm(total_base_hours)
    workpack_days = report_data.get('workpack_days')
    start_date = report_data.get('start_date')
    end_date = report_data.get('end_date')

    # Add workpack information header if available
    if start_date and end_date and workpack_days:
        data.append(['Workpack Period:', f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                     f"{workpack_days} days", ''])
        data.append(['', '', '', ''])  # Empty row for spacing

    # Show base vs adjusted totals
    data.append(['Man-Hours Summary', '', '', ''])
    data.append(['Base Man-Hours (before coefficient):', total_base_time_str, '', ''])
    data.append(['Adjusted Man-Hours (with coefficient):', total_time_str, '', ''])
    data.append(['', '', '', ''])  # Empty row for spacing

    # Add column headers
    if workpack_days:
        data.append(['Special Code', 'Hours (HH:MM)', 'Avg Hours/Day (HH:MM)', 'Distribution (%)'])
    else:
        data.append(['Special Code', 'Hours (HH:MM)', 'Distribution (%)'])

    if report_data['enable_special_code'] and report_data['special_code_distribution']:
        special_code_per_day = report_data.get('special_code_per_day', {})

        # Add each special code row
        for code, hours in report_data['special_code_distribution'].items():
            code_str = str(code) if pd.notna(code) else "(No Code)"
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            time_str = hours_to_hhmm(hours)

            if workpack_days and code in special_code_per_day:
                avg_per_day_str = hours_to_hhmm(special_code_per_day[code])
                data.append([code_str, time_str, avg_per_day_str, f"{percentage:.1f}%"])
            else:
                data.append([code_str, time_str, f"{percentage:.1f}%"])

    # Add Total row at the end
    if workpack_days:
        avg_total_per_day = total_hours / workpack_days if workpack_days > 0 else 0
        avg_total_str = hours_to_hhmm(avg_total_per_day)
        data.append(['Total', total_time_str, avg_total_str, '100.0%'])
    else:
        data.append(['Total', total_time_str, '100.0%'])

    # Create DataFrame and write to Excel
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Total Man-Hours', index=False, header=False)

    # Auto-adjust column widths
    worksheet = writer.sheets['Total Man-Hours']
    for idx in range(len(df.columns)):
        max_length = max(
            df.iloc[:, idx].astype(str).apply(len).max(),
            15  # Minimum width
        )
        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2


def create_high_mhrs_sheet(writer, report_data):
    """Create the High Man-Hours Tasks sheet with coefficient info"""
    high_mhrs_df = report_data['high_mhrs_tasks'].copy()

    if len(high_mhrs_df) == 0:
        # Create empty sheet with message
        df = pd.DataFrame([['No tasks found with planned man-hours exceeding the threshold']])
        df.to_excel(writer, sheet_name='High Man-Hours Tasks', index=False, header=False)
        return

    # Add HH:MM formatted columns for both base and adjusted hours
    high_mhrs_df['Base Mhrs (HH:MM)'] = high_mhrs_df['Base Hours'].apply(hours_to_hhmm)
    high_mhrs_df['Adjusted Mhrs (HH:MM)'] = high_mhrs_df['Adjusted Hours'].apply(hours_to_hhmm)

    # Select and order columns
    columns_to_export = []

    # Add SEQ_NO_COLUMN if it exists
    if SEQ_NO_COLUMN in high_mhrs_df.columns:
        columns_to_export.append(SEQ_NO_COLUMN)

    # Add TITLE_COLUMN if it exists
    if TITLE_COLUMN in high_mhrs_df.columns:
        columns_to_export.append(TITLE_COLUMN)

    # Add Task ID if it exists
    if 'Task ID' in high_mhrs_df.columns:
        columns_to_export.append('Task ID')

    # Add coefficient and hour columns
    columns_to_export.extend(['Coefficient', 'Base Mhrs (HH:MM)', 'Adjusted Mhrs (HH:MM)'])

    export_df = high_mhrs_df[columns_to_export]

    # Write to Excel
    export_df.to_excel(writer, sheet_name='High Man-Hours Tasks', index=False)

    # Auto-adjust column widths
    worksheet = writer.sheets['High Man-Hours Tasks']
    for idx, col in enumerate(export_df.columns):
        max_length = max(
            export_df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)


def create_new_task_ids_sheet(writer, report_data):
    """Create the New Task IDs sheet with SEQ numbers"""
    new_task_ids_df = report_data['new_task_ids_with_seq']

    if len(new_task_ids_df) == 0:
        # Create empty sheet with message
        df = pd.DataFrame([['No new task IDs found - all task IDs match reference']])
        df.to_excel(writer, sheet_name='New Task IDs', index=False, header=False)
        return

    # Filter out None and 'nan' values
    filtered_df = new_task_ids_df[
        new_task_ids_df['Task ID'].notna() &
        (new_task_ids_df['Task ID'].astype(str) != 'nan')
        ].copy()

    if len(filtered_df) == 0:
        df = pd.DataFrame([['No new task IDs found - all task IDs match reference']])
        df.to_excel(writer, sheet_name='New Task IDs', index=False, header=False)
        return

    # Rename columns for clarity
    filtered_df.columns = ['SEQ', 'New Task ID']

    # Write to Excel
    filtered_df.to_excel(writer, sheet_name='New Task IDs', index=False)

    # Auto-adjust column widths
    worksheet = writer.sheets['New Task IDs']
    for idx, col in enumerate(filtered_df.columns):
        max_length = max(
            filtered_df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2


def save_debug_log(base_filename, timestamp, report_data):
    """Save debug information to LOG folder"""
    # Create LOG folder in root directory
    log_folder = os.path.join(os.getcwd(), 'LOG')
    os.makedirs(log_folder, exist_ok=True)

    # Create subfolder for this file
    file_log_folder = os.path.join(log_folder, base_filename)
    os.makedirs(file_log_folder, exist_ok=True)

    # Define log file path
    log_file_path = os.path.join(file_log_folder, f"debug_{timestamp}.txt")

    # Write debug information
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("DEBUG LOG\n")
        f.write("=" * 60 + "\n")
        f.write(f"File: {base_filename}\n")
        f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Add workpack info if available
        if report_data.get('start_date') and report_data.get('end_date'):
            f.write(
                f"Workpack Period: {report_data['start_date'].strftime('%Y-%m-%d')} to {report_data['end_date'].strftime('%Y-%m-%d')}\n")
            f.write(f"Workpack Duration: {report_data.get('workpack_days', 'N/A')} days\n")

        # Add man-hours summary
        f.write("\nMan-Hours Summary:\n")
        f.write(f"Base Man-Hours: {report_data.get('total_base_mhrs_hhmm', 'N/A')}\n")
        f.write(f"Adjusted Man-Hours (with coefficients): {report_data['total_mhrs_hhmm']}\n")

        f.write("=" * 60 + "\n\n")

        # Debug sample
        debug_df = report_data['debug_sample']

        if len(debug_df) == 0:
            f.write("No data to display (all rows were ignored)\n")
            return

        f.write(f"DEBUG SAMPLE REPORT (Random {len(debug_df)} Rows):\n")
        f.write("-" * 110 + "\n")

        if report_data['enable_special_code']:
            f.write(
                f"| {SEQ_NO_COLUMN:<8} | Special Code | Task ID          | Coeff | Base Mhrs | Adjusted Mhrs |\n")
            f.write("-" * 110 + "\n")
            for index, row in debug_df.iterrows():
                seq_no = str(row[SEQ_NO_COLUMN])
                special_code = str(row.get('Special code', 'N/A')) if pd.notna(row.get('Special code')) else "N/A"
                special_code = special_code[:12]
                task_id = str(row['Task ID'])[:16]
                coefficient = row.get('Coefficient', 1.0)
                base_hours = row.get('Base Hours', 0)
                adjusted_hours = row.get('Adjusted Hours', 0)
                base_time_hhmm = hours_to_hhmm(base_hours)
                adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)
                f.write(
                    f"| {seq_no:<8} | {special_code:<12} | {task_id:<16} | {coefficient:<5.1f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |\n")
        else:
            f.write(
                f"| {SEQ_NO_COLUMN:<8} | {TITLE_COLUMN[:30]:<30} | Task ID          | Coeff | Base Mhrs | Adjusted Mhrs |\n")
            f.write("-" * 115 + "\n")
            for index, row in debug_df.iterrows():
                seq_no = str(row[SEQ_NO_COLUMN])
                title = str(row[TITLE_COLUMN])[:30]
                task_id = str(row['Task ID'])[:16]
                coefficient = row.get('Coefficient', 1.0)
                base_hours = row.get('Base Hours', 0)
                adjusted_hours = row.get('Adjusted Hours', 0)
                base_time_hhmm = hours_to_hhmm(base_hours)
                adjusted_time_hhmm = hours_to_hhmm(adjusted_hours)
                f.write(
                    f"| {seq_no:<8} | {title:<30} | {task_id:<16} | {coefficient:<5.1f} | {base_time_hhmm:>9} | {adjusted_time_hhmm:>13} |\n")

        f.write("-" * 110 + "\n")

    print(f"Debug log saved to {log_file_path}")


def create_tool_control_sheet(writer, report_data):
    """Create the Tool Control sheet showing tools/spares with zero availability"""
    tool_issues_df = report_data.get('tool_control_issues', pd.DataFrame())

    if len(tool_issues_df) == 0:
        # Create empty sheet with message
        df = pd.DataFrame([['All tools and spares have adequate availability (quantity > 0)']])
        df.to_excel(writer, sheet_name='Tool Control', index=False, header=False)
        return

    # Write to Excel with headers
    tool_issues_df.to_excel(writer, sheet_name='Tool Control', index=False)

    # Auto-adjust column widths
    worksheet = writer.sheets['Tool Control']
    for idx, col in enumerate(tool_issues_df.columns):
        max_length = max(
            tool_issues_df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        # Set appropriate width based on column
        if col == 'Tool/Spare Name':
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 70)
        elif col == 'Part Number':
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 25)
        elif col == 'Task ID':
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 30)
        else:
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 20)


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