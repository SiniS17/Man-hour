"""
Total Man-Hours Sheet Module
UPDATED: Restructured output, removed decimal hours, added Worker calculations
"""

import pandas as pd
import math
from utils.time_utils import hours_to_hhmm
from core.config import HOURS_PER_SHIFT


def create_total_mhrs_sheet(writer, report_data):
    """
    Create TWO separate sheets:
    1. Total Man-Hours Summary
    2. Special Code Distribution
    """
    create_man_hours_summary_sheet(writer, report_data)

    if report_data.get('enable_special_code'):
        create_special_code_sheet(writer, report_data)


def create_man_hours_summary_sheet(writer, report_data):
    """
    Create the Total Man-Hours Summary sheet.

    New Structure:
    1. Project Information
    2. Base Man-Hours (before any adjustments)
    3. Bonus Hours (breakdown by source)
    4. Total Man-Hours (Base + Coefficients + Bonus)
    """
    data = []

    total_mhrs = report_data['total_mhrs']
    total_base_mhrs = report_data.get('total_base_mhrs', total_mhrs)
    coefficient_effect = report_data.get('coefficient_effect', 0.0)
    bonus_hours = report_data.get('bonus_hours', 0.0)

    workpack_days = report_data.get('workpack_days')
    start_date = report_data.get('start_date')
    end_date = report_data.get('end_date')

    ac_type = report_data.get('ac_type')
    ac_name = report_data.get('ac_name')
    wp_type = report_data.get('wp_type')

    # === PROJECT INFORMATION ===
    data.append(['PROJECT INFORMATION', ''])
    data.append(['Workpack Period:',
                 f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}" if start_date and end_date else 'N/A'])
    data.append(['Workpack Duration:',
                 f"{workpack_days} days" if workpack_days else 'N/A'])
    data.append(['Aircraft Registration:', ac_name or 'N/A'])
    data.append(['Aircraft Type:', ac_type or 'N/A'])
    data.append(['Check Type (WP Type):', wp_type or 'N/A'])
    data.append(['', ''])

    # === BASE MAN-HOURS ===
    data.append(['BASE MAN-HOURS', ''])
    data.append(['(Before any coefficients or bonus)', ''])
    data.append(['Base Man-Hours:', hours_to_hhmm(total_base_mhrs)])
    data.append(['', ''])

    # === BONUS HOURS ===
    data.append(['BONUS HOURS', ''])
    bonus_breakdown = report_data.get('bonus_breakdown', {})

    if bonus_breakdown:
        for source, hours in bonus_breakdown.items():
            data.append([f"  • {source}", hours_to_hhmm(hours)])
        data.append(['', ''])

    data.append(['Total Bonus Hours:', hours_to_hhmm(bonus_hours)])
    data.append(['', ''])

    # === TOTAL MAN-HOURS ===
    data.append(['TOTAL MAN-HOURS', ''])
    data.append(['(Base + SEQ Coefficients + Bonus)', ''])
    data.append(['Total Man-Hours:', hours_to_hhmm(total_mhrs)])

    if workpack_days and workpack_days > 0:
        avg_per_day = total_mhrs / workpack_days
        data.append(['Average Man-Hours per Day:', hours_to_hhmm(avg_per_day)])

        # Calculate Average Worker per Day (rounded down)
        avg_worker_per_day = math.floor(avg_per_day / HOURS_PER_SHIFT)
        data.append(['Average Worker per Day:', f"{avg_worker_per_day} worker(s)"])

    # Create DataFrame and write
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Total Man-Hours Summary', index=False, header=False)

    # Format worksheet
    worksheet = writer.sheets['Total Man-Hours Summary']
    worksheet.column_dimensions['A'].width = 45
    worksheet.column_dimensions['B'].width = 20


def create_special_code_sheet(writer, report_data):
    """
    Create the Special Code Distribution sheet.
    UPDATED: Removed decimal hours, added Worker(s)/Day calculation (rounded down).
    """
    data = []

    total_hours = report_data['total_mhrs']
    workpack_days = report_data.get('workpack_days')

    # Header row
    if workpack_days:
        data.append(['Special Code', 'Hours', 'Avg Hours/Day', 'Worker(s)/Day', 'Distribution (%)'])
    else:
        data.append(['Special Code', 'Hours', 'Distribution (%)'])

    if report_data['special_code_distribution']:
        special_code_per_day = report_data.get('special_code_per_day', {})

        # Add each special code row
        for code, hours in report_data['special_code_distribution'].items():
            code_str = str(code) if pd.notna(code) else "(No Code)"
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            time_str = hours_to_hhmm(hours)

            if workpack_days and code in special_code_per_day:
                avg_per_day = special_code_per_day[code]
                avg_per_day_str = hours_to_hhmm(avg_per_day)
                # Round DOWN to nearest integer
                worker_per_day = math.floor(avg_per_day / HOURS_PER_SHIFT)
                data.append([code_str, time_str, avg_per_day_str, worker_per_day, f"{percentage:.1f}%"])
            else:
                data.append([code_str, time_str, f"{percentage:.1f}%"])

    # Add Total row
    if workpack_days:
        avg_total_per_day = total_hours / workpack_days if workpack_days > 0 else 0
        avg_total_str = hours_to_hhmm(avg_total_per_day)
        # Round DOWN to nearest integer
        worker_total_per_day = math.floor(avg_total_per_day / HOURS_PER_SHIFT)
        data.append(['TOTAL', hours_to_hhmm(total_hours), avg_total_str, worker_total_per_day, '100.0%'])
    else:
        data.append(['TOTAL', hours_to_hhmm(total_hours), '100.0%'])

    # Create DataFrame and write
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Special Code Distribution', index=False, header=False)

    # Format worksheet
    worksheet = writer.sheets['Special Code Distribution']
    worksheet.auto_filter.ref = f"A1:{chr(65 + len(data[0]) - 1)}{len(data)}"

    # Adjust column widths
    for idx in range(len(data[0])):
        col_letter = chr(65 + idx)
        if idx == 0:  # Special Code
            worksheet.column_dimensions[col_letter].width = 25
        elif idx == 3:  # Worker(s)/Day
            worksheet.column_dimensions[col_letter].width = 15
        else:
            worksheet.column_dimensions[col_letter].width = 20