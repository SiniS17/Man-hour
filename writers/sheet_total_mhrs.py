"""
Total Man-Hours Sheet Module
UPDATED: Simplified layout to match desired output format
"""

import pandas as pd
import math
from utils.time_utils import hours_to_hhmm
from core.config import HOURS_PER_SHIFT


def format_worker_per_day(avg_hours_per_day, hours_per_shift=8):
    """
    Format worker per day display.
    If less than 1 full worker (< 8 hours/day), show "< 8h/day" instead of "0 worker(s)"

    Args:
        avg_hours_per_day: Average hours per day
        hours_per_shift: Hours per shift (default 8)

    Returns:
        str: Formatted worker display
    """
    worker_count = avg_hours_per_day / hours_per_shift

    if worker_count < 1:
        return "< 8h/day"
    else:
        return f"{math.floor(worker_count)} worker(s)"


def create_total_mhrs_sheet(writer, report_data):
    """
    Create the Total Man-Hours Summary sheet with simplified layout.

    Structure:
    1. Project Information (3 rows only)
    2. Special Code Distribution Table
    """
    data = []

    total_mhrs = report_data['total_mhrs']
    workpack_days = report_data.get('workpack_days')
    start_date = report_data.get('start_date')
    end_date = report_data.get('end_date')

    # === PROJECT INFORMATION (simplified) ===
    data.append(['PROJECT INFORMATION', ''])
    data.append(['Workpack Period:',
                 f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}" if start_date and end_date else 'N/A'])
    data.append(['Workpack Duration:',
                 f"{workpack_days} days" if workpack_days else 'N/A'])
    data.append(['Total Man-Hours:', hours_to_hhmm(total_mhrs)])
    data.append(['', ''])

    # === SPECIAL CODE DISTRIBUTION TABLE ===
    if report_data.get('enable_special_code') and report_data.get('special_code_distribution'):
        # Table header
        if workpack_days:
            data.append(['Special Code', 'Hours', 'Avg Hours/Day', 'Worker(s)/Day', 'Distribution (%)'])
        else:
            data.append(['Special Code', 'Hours', 'Distribution (%)'])

        special_code_per_day = report_data.get('special_code_per_day', {})

        # Add each special code row
        for code, hours in report_data['special_code_distribution'].items():
            code_str = str(code) if pd.notna(code) else "(No Code)"
            percentage = (hours / total_mhrs * 100) if total_mhrs > 0 else 0
            time_str = hours_to_hhmm(hours)

            if workpack_days and code in special_code_per_day:
                avg_per_day = special_code_per_day[code]
                avg_per_day_str = hours_to_hhmm(avg_per_day)
                worker_display = format_worker_per_day(avg_per_day, HOURS_PER_SHIFT)
                data.append([code_str, time_str, avg_per_day_str, worker_display, f"{percentage:.1f}%"])
            else:
                data.append([code_str, time_str, f"{percentage:.1f}%"])

        # Add Total row
        if workpack_days:
            avg_total_per_day = total_mhrs / workpack_days if workpack_days > 0 else 0
            avg_total_str = hours_to_hhmm(avg_total_per_day)
            worker_total_display = format_worker_per_day(avg_total_per_day, HOURS_PER_SHIFT)
            data.append(['TOTAL', hours_to_hhmm(total_mhrs), avg_total_str, worker_total_display, '100.0%'])
        else:
            data.append(['TOTAL', hours_to_hhmm(total_mhrs), '100.0%'])

    # Create DataFrame and write
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Total Man-Hours Summary', index=False, header=False)

    # Format worksheet
    worksheet = writer.sheets['Total Man-Hours Summary']

    # Adjust column widths
    worksheet.column_dimensions['A'].width = 25
    worksheet.column_dimensions['B'].width = 20
    worksheet.column_dimensions['C'].width = 20
    worksheet.column_dimensions['D'].width = 20
    worksheet.column_dimensions['E'].width = 20

    # Add autofilter to the special code table if it exists
    if report_data.get('enable_special_code') and report_data.get('special_code_distribution'):
        # Find the row where the table header starts (row with "Special Code")
        table_start_row = None
        for idx, row in enumerate(data, start=1):
            if row[0] == 'Special Code':
                table_start_row = idx
                break

        if table_start_row:
            num_cols = 5 if workpack_days else 3
            table_end_row = len(data)
            worksheet.auto_filter.ref = f"A{table_start_row}:{chr(64 + num_cols)}{table_end_row}"