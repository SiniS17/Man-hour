"""
Bonus Hours Sheet Module
Generates the Bonus Hours breakdown sheet
Place this file in: writers/sheet_bonus_hours.py
"""

import pandas as pd
from utils.time_utils import hours_to_hhmm


def create_bonus_hours_sheet(writer, report_data):
    """
    Create the Bonus Hours Breakdown sheet.

    Shows a table with columns: "Bonus From" | "Bonus Mhr"
    Where "Bonus From" is the sheet name and "Bonus Mhr" is the total bonus hours

    Args:
        writer: pd.ExcelWriter object
        report_data (dict): Dictionary containing processed data
    """
    bonus_breakdown = report_data.get('bonus_breakdown', [])

    if not bonus_breakdown or len(bonus_breakdown) == 0:
        # Create empty sheet with message
        df = pd.DataFrame([['No bonus hours applied for this workpack']])
        df.to_excel(writer, sheet_name='Bonus Hours', index=False, header=False)
        return

    # Create DataFrame from breakdown list
    # Format: [{'bonus_from': sheet_name, 'bonus_mhr': hours}, ...]

    data = []
    for item in bonus_breakdown:
        bonus_from = item['bonus_from']
        bonus_hours = item['bonus_mhr']
        bonus_hours_hhmm = hours_to_hhmm(bonus_hours)

        data.append({
            'Bonus From': bonus_from,
            'Bonus Mhr': bonus_hours_hhmm
        })

    # Add total row
    total_bonus = sum(item['bonus_mhr'] for item in bonus_breakdown)
    total_bonus_hhmm = hours_to_hhmm(total_bonus)

    data.append({
        'Bonus From': 'Total',
        'Bonus Mhr': total_bonus_hhmm
    })

    df = pd.DataFrame(data)

    # Write to Excel
    df.to_excel(writer, sheet_name='Bonus Hours', index=False)

    # Get the worksheet
    worksheet = writer.sheets['Bonus Hours']

    # Add autofilter to headers (excluding total row)
    if len(df) > 1:
        filter_range = f"A1:B{len(df)}"  # Include total in filter range
        worksheet.auto_filter.ref = filter_range

    # Auto-adjust column widths
    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(str(col))
        )
        # Give extra space for "Bonus From" column
        if col == 'Bonus From':
            max_length = max(max_length, 30)

        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

    print(f"  Created Bonus Hours sheet with {len(bonus_breakdown)} entries")


def get_bonus_hours_summary(bonus_breakdown):
    """
    Generate a summary of bonus hours.

    Args:
        bonus_breakdown (list): List of bonus hour dictionaries

    Returns:
        dict: Summary statistics
    """
    if not bonus_breakdown:
        return {
            'total_sheets': 0,
            'total_bonus_hours': 0.0
        }

    return {
        'total_sheets': len(bonus_breakdown),
        'total_bonus_hours': sum(item['bonus_mhr'] for item in bonus_breakdown)
    }


def format_bonus_breakdown_for_display(bonus_breakdown):
    """
    Format bonus breakdown for console display.

    Args:
        bonus_breakdown (list): List of bonus hour dictionaries

    Returns:
        str: Formatted string for display
    """
    if not bonus_breakdown:
        return "No bonus hours applied"

    lines = []
    lines.append("Bonus Hours Breakdown:")
    lines.append("-" * 50)

    for item in bonus_breakdown:
        bonus_from = item['bonus_from']
        bonus_hours = item['bonus_mhr']
        bonus_hhmm = hours_to_hhmm(bonus_hours)
        lines.append(f"  {bonus_from}: {bonus_hhmm}")

    total = sum(item['bonus_mhr'] for item in bonus_breakdown)
    total_hhmm = hours_to_hhmm(total)
    lines.append("-" * 50)
    lines.append(f"  Total: {total_hhmm}")

    return "\n".join(lines)