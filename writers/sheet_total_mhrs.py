"""
Total Man-Hours Sheet Module
Generates the Total Man-Hours sheet with special code distribution and bonus hours breakdown
"""

import pandas as pd
from utils.time_utils import hours_to_hhmm
from core.config import SHOW_BONUS_HOURS_BREAKDOWN


def create_total_mhrs_sheet(writer, report_data):
    """
    Create the Total Man-Hours sheet with:
    1. Project Information Header
    2. Addition from (coefficient and bonus) - NO FILTER
    3. Special Code Distribution - WITH FILTER

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    data = []

    total_hours = report_data['total_mhrs']
    total_base_hours = report_data.get('total_base_mhrs', total_hours)
    bonus_hours = report_data.get('bonus_hours', 0.0)
    coefficient_hours = report_data.get('coefficient_hours', 0.0)

    workpack_days = report_data.get('workpack_days')
    start_date = report_data.get('start_date')
    end_date = report_data.get('end_date')

    ac_type = report_data.get('ac_type')
    ac_name = report_data.get('ac_name')
    wp_type = report_data.get('wp_type')

    # === PROJECT INFORMATION HEADER ===
    data.append(['Workpack Period:', f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}" if start_date and end_date else 'N/A', f"{workpack_days} days" if workpack_days else 'N/A'])
    data.append(['Aircraft Registration:', ac_name or 'N/A', ''])
    data.append(['Aircraft Type:', ac_type or 'N/A', ''])
    data.append(['Check Type (WP Type):', wp_type or 'N/A', ''])
    data.append(['Base Man-Hours:', hours_to_hhmm(total_base_hours), ''])
    data.append(['', '', ''])  # Empty row

    # === ADDITION FROM TABLE (NO FILTER) ===
    data.append(['Addition from', 'Additional Man-Hour'])

    # Get bonus breakdown by source
    bonus_breakdown = report_data.get('bonus_breakdown', {})

    # Add each bonus source
    for source, hours in bonus_breakdown.items():
        if hours > 0:
            data.append([source, f"{hours:.1f}"])

    # Add SEQ coefficient row
    if coefficient_hours > 0:
        data.append(['SEQ coefficient', f"{coefficient_hours:.1f}"])

    # Calculate total additional
    total_additional = sum(bonus_breakdown.values()) + (coefficient_hours if coefficient_hours > 0 else 0)
    data.append(['Total', f"{total_additional:.1f}"])

    data.append(['', ''])  # Empty row

    # Track where special code table starts for filter
    special_code_start_row = len(data) + 1

    # === SPECIAL CODE DISTRIBUTION TABLE (WITH FILTER) ===
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

    # Add Total row for special codes
    if workpack_days:
        avg_total_per_day = total_hours / workpack_days if workpack_days > 0 else 0
        avg_total_str = hours_to_hhmm(avg_total_per_day)
        data.append(['Total', hours_to_hhmm(total_hours), avg_total_str, '100.0%'])
    else:
        data.append(['Total', hours_to_hhmm(total_hours), '100.0%'])

    # Create DataFrame and write to Excel
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Total Man-Hours', index=False, header=False)

    # Get the worksheet
    worksheet = writer.sheets['Total Man-Hours']

    # Add autofilter ONLY to the special code table
    special_code_end_row = len(data)
    num_cols = df.shape[1]

    if workpack_days:
        filter_range = f"A{special_code_start_row}:D{special_code_end_row}"
    else:
        filter_range = f"A{special_code_start_row}:C{special_code_end_row}"

    try:
        worksheet.auto_filter.ref = filter_range
    except:
        pass  # Skip if filter fails

    # Auto-adjust column widths
    for idx in range(num_cols):
        try:
            max_length = max(
                df.iloc[:, idx].astype(str).apply(len).max(),
                15  # Minimum width
            )
            col_letter = chr(65 + idx)
            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
        except:
            pass  # Skip if column adjustment fails


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