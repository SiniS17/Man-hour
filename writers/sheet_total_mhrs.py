"""
Total Man-Hours Sheet Module
Generates the Total Man-Hours sheet with special code distribution
"""

import pandas as pd
from utils.time_utils import hours_to_hhmm


def create_total_mhrs_sheet(writer, report_data):
    """
    Create the Total Man-Hours sheet with Special Code distribution and average per day.

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
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


def format_workpack_header(start_date, end_date, workpack_days):
    """
    Format the workpack period header.

    Args:
        start_date: Start date
        end_date: End date
        workpack_days (int): Number of days

    Returns:
        list: Formatted row for workpack header
    """
    date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    days_str = f"{workpack_days} days"
    return ['Workpack Period:', date_range, days_str, '']


def calculate_percentage(hours, total_hours):
    """
    Calculate percentage of total hours.

    Args:
        hours (float): Hours for this item
        total_hours (float): Total hours

    Returns:
        float: Percentage
    """
    if total_hours <= 0:
        return 0.0
    return (hours / total_hours) * 100