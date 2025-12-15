"""
Total Man-Hours Sheet Module
Generates TWO separate sheets:
1. Total Man-Hours Summary (bonus breakdown and type coefficient breakdown)
2. Special Code Distribution (special code analysis)
"""

import pandas as pd
from utils.time_utils import hours_to_hhmm
from core.config import SHOW_BONUS_HOURS_BREAKDOWN


def create_total_mhrs_sheet(writer, report_data):
    """
    Create TWO separate sheets:
    1. Total Man-Hours Summary
    2. Special Code Distribution

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    # Sheet 1: Total Man-Hours Summary
    create_man_hours_summary_sheet(writer, report_data)

    # Sheet 2: Special Code Distribution
    if report_data.get('enable_special_code'):
        create_special_code_sheet(writer, report_data)


def create_man_hours_summary_sheet(writer, report_data):
    """
    Create the Total Man-Hours Summary sheet with project info, bonus breakdown, and type coefficient breakdown.

    Layout:
    1. Project Information Header
    2. Base Man-Hours
    3. Additional Hours Breakdown (Bonus + Type Coefficient)
    4. Final Total

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    data = []

    total_hours = report_data['total_mhrs']
    total_base_hours = report_data.get('total_base_mhrs', total_hours)
    bonus_hours = report_data.get('bonus_hours', 0.0)
    type_coefficient_hours = report_data.get('type_coefficient_hours', 0.0)

    workpack_days = report_data.get('workpack_days')
    start_date = report_data.get('start_date')
    end_date = report_data.get('end_date')

    ac_type = report_data.get('ac_type')
    ac_name = report_data.get('ac_name')
    wp_type = report_data.get('wp_type')

    # === PROJECT INFORMATION HEADER ===
    data.append(['PROJECT INFORMATION', '', ''])
    data.append(['Workpack Period:',
                 f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}" if start_date and end_date else 'N/A',
                 f"{workpack_days} days" if workpack_days else 'N/A'])
    data.append(['Aircraft Registration:', ac_name or 'N/A', ''])
    data.append(['Aircraft Type:', ac_type or 'N/A', ''])
    data.append(['Check Type (WP Type):', wp_type or 'N/A', ''])
    data.append(['', '', ''])  # Empty row

    # === BASE MAN-HOURS ===
    data.append(['MAN-HOURS CALCULATION', '', ''])
    data.append(['Base Man-Hours:', hours_to_hhmm(total_base_hours), f"{total_base_hours:.2f}"])
    data.append(['', '', ''])  # Empty row

    # === ADDITIONAL HOURS BREAKDOWN ===
    data.append(['ADDITIONAL HOURS BREAKDOWN', 'HH:MM', 'Hours'])

    additional_total = 0.0

    # 1. Bonus Hours Breakdown
    bonus_breakdown = report_data.get('bonus_breakdown', {})
    if bonus_breakdown:
        data.append(['Bonus Hours:', '', ''])
        for source, hours in bonus_breakdown.items():
            if hours > 0:
                data.append([f"  • {source}", hours_to_hhmm(hours), f"{hours:.2f}"])
                additional_total += hours
        data.append(['', '', ''])  # Empty row after bonus section

    # 2. Type Coefficient Breakdown
    type_coeff_breakdown = report_data.get('type_coeff_breakdown', {})
    if type_coeff_breakdown:
        data.append(['Type Coefficient Adjustments:', '', ''])
        for special_type, info in type_coeff_breakdown.items():
            additional_hours = info.get('additional_hours', 0)
            coefficient = info.get('coefficient', 1.0)
            count = info.get('count', 0)
            if additional_hours != 0:  # Show both positive and negative adjustments
                label = f"  • {special_type} (Coeff: {coefficient:.2f}, {count} tasks)"
                data.append([label, hours_to_hhmm(additional_hours), f"{additional_hours:.2f}"])
                additional_total += additional_hours
        data.append(['', '', ''])  # Empty row after type coefficient section
    elif type_coefficient_hours > 0:
        # If no breakdown but has coefficient hours, show total
        data.append(['Type Coefficient Adjustments:', hours_to_hhmm(type_coefficient_hours), f"{type_coefficient_hours:.2f}"])
        additional_total += type_coefficient_hours
        data.append(['', '', ''])  # Empty row

    # Subtotal of additional hours
    data.append(['Total Additional Hours:', hours_to_hhmm(additional_total), f"{additional_total:.2f}"])
    data.append(['', '', ''])  # Empty row

    # === FINAL TOTAL ===
    data.append(['FINAL TOTAL', '', ''])
    data.append(['Total Man-Hours:', hours_to_hhmm(total_hours), f"{total_hours:.2f}"])

    # Add average per day if workpack days available
    if workpack_days and workpack_days > 0:
        avg_per_day = total_hours / workpack_days
        data.append(['Average Man-Hours per Day:', hours_to_hhmm(avg_per_day), f"{avg_per_day:.2f}"])

    # Create DataFrame and write to Excel
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Total Man-Hours Summary', index=False, header=False)

    # Format the worksheet
    worksheet = writer.sheets['Total Man-Hours Summary']

    # Auto-adjust column widths
    worksheet.column_dimensions['A'].width = 45
    worksheet.column_dimensions['B'].width = 20
    worksheet.column_dimensions['C'].width = 15


def create_special_code_sheet(writer, report_data):
    """
    Create the Special Code Distribution sheet with filtering capability.

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    data = []

    total_hours = report_data['total_mhrs']
    workpack_days = report_data.get('workpack_days')

    # Add header based on whether we have workpack days
    if workpack_days:
        data.append(['Special Code', 'Hours (HH:MM)', 'Hours (Decimal)', 'Avg Hours/Day (HH:MM)', 'Avg Hours/Day (Decimal)', 'Distribution (%)'])
    else:
        data.append(['Special Code', 'Hours (HH:MM)', 'Hours (Decimal)', 'Distribution (%)'])

    if report_data['special_code_distribution']:
        special_code_per_day = report_data.get('special_code_per_day', {})

        # Add each special code row
        for code, hours in report_data['special_code_distribution'].items():
            code_str = str(code) if pd.notna(code) else "(No Code)"
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            time_str = hours_to_hhmm(hours)
            hours_decimal = f"{hours:.2f}"

            if workpack_days and code in special_code_per_day:
                avg_per_day = special_code_per_day[code]
                avg_per_day_str = hours_to_hhmm(avg_per_day)
                avg_per_day_decimal = f"{avg_per_day:.2f}"
                data.append([code_str, time_str, hours_decimal, avg_per_day_str, avg_per_day_decimal, f"{percentage:.1f}%"])
            else:
                data.append([code_str, time_str, hours_decimal, f"{percentage:.1f}%"])

    # Add Total row
    if workpack_days:
        avg_total_per_day = total_hours / workpack_days if workpack_days > 0 else 0
        avg_total_str = hours_to_hhmm(avg_total_per_day)
        avg_total_decimal = f"{avg_total_per_day:.2f}"
        data.append(['TOTAL', hours_to_hhmm(total_hours), f"{total_hours:.2f}", avg_total_str, avg_total_decimal, '100.0%'])
    else:
        data.append(['TOTAL', hours_to_hhmm(total_hours), f"{total_hours:.2f}", '100.0%'])

    # Create DataFrame and write to Excel
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Special Code Distribution', index=False, header=False)

    # Get the worksheet
    worksheet = writer.sheets['Special Code Distribution']

    # Add autofilter to the entire table
    worksheet.auto_filter.ref = f"A1:{chr(65 + len(data[0]) - 1)}{len(data)}"

    # Auto-adjust column widths
    for idx in range(len(data[0])):
        col_letter = chr(65 + idx)
        if idx == 0:  # Special Code column
            worksheet.column_dimensions[col_letter].width = 25
        else:
            worksheet.column_dimensions[col_letter].width = 20