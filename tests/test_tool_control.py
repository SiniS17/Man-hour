"""
Tool Control Test Module
Tests tool control functionality with sample data
"""

import pandas as pd
from core.config import (ENABLE_TOOL_CONTROL, TOOL_NAME_COLUMN, TOOL_TYPE_COLUMN,
                         TOOL_PARTNO_COLUMN, TOTAL_QTY_COLUMN, ALT_QTY_COLUMN,
                         SEQ_NO_COLUMN, TITLE_COLUMN, SEQ_MAPPINGS, SEQ_ID_MAPPINGS)

if ENABLE_TOOL_CONTROL:
    from features.tool_control import check_tool_availability, get_tool_control_summary


def test_tool_control():
    """
    Test the tool control checking logic with sample data.

    Returns:
        dict: Test result with status and details
    """
    result = {
        'passed': True,
        'errors': [],
        'warnings': [],
        'output': []
    }

    result['output'].append("Testing Tool Control Functionality...")
    result['output'].append("")

    # Check if tool control is enabled
    result['output'].append(f"Tool Control Enabled: {ENABLE_TOOL_CONTROL}")

    if not ENABLE_TOOL_CONTROL:
        result['warnings'].append("Tool control is disabled in settings.ini")
        result['output'].append("⚠ Tool control is disabled - skipping tests")
        return result

    # Check configuration
    result['output'].append(f"Tool Name Column: {TOOL_NAME_COLUMN}")
    result['output'].append(f"Tool Type Column: {TOOL_TYPE_COLUMN}")
    result['output'].append(f"Tool Part No Column: {TOOL_PARTNO_COLUMN}")
    result['output'].append(f"Total Qty Column: {TOTAL_QTY_COLUMN}")
    result['output'].append(f"Alt Qty Column: {ALT_QTY_COLUMN}")
    result['output'].append("")

    # Create sample data
    result['output'].append("Creating sample test data...")
    df = create_sample_data()

    result['output'].append(f"Sample data created: {len(df)} rows")
    result['output'].append("")

    # Apply tool control logic
    result['output'].append("Applying Tool Control Logic...")
    result['output'].append("Processing EVERY row independently - NO deduplication")
    result['output'].append("")

    try:
        issues = check_tool_availability(df, SEQ_MAPPINGS, SEQ_ID_MAPPINGS)

        result['output'].append("RESULTS - Items with ZERO availability:")
        result['output'].append("=" * 80)

        if len(issues) > 0:
            result['output'].append(f"Found {len(issues)} tool/spare items with zero availability")
            result['output'].append("")

            # Show results
            for idx, row in issues.iterrows():
                result['output'].append(
                    f"Row {idx + 1}: SEQ {row['SEQ']}, Part {row['Part Number']}, "
                    f"{row['Tool/Spare Name']}, Type: {row['Type']}"
                )

            result['output'].append("")

            # Get summary
            summary = get_tool_control_summary(issues)
            result['output'].append("Summary:")
            result['output'].append(f"  Total issues: {summary['total_issues']}")
            result['output'].append(f"  - Tools: {summary['total_tools']}")
            result['output'].append(f"  - Spares: {summary['total_spares']}")
            result['output'].append(f"  Unique part numbers: {summary['unique_parts']}")
            result['output'].append(f"  Affected SEQs: {summary['affected_seqs']}")

            # Validate expected results
            expected_issues = 5  # Based on sample data
            if len(issues) == expected_issues:
                result['output'].append("")
                result['output'].append(f"✓ Found expected number of issues ({expected_issues})")
                result['passed'] = True
            else:
                result['output'].append("")
                result['output'].append(f"✗ Expected {expected_issues} issues, found {len(issues)}")
                result['errors'].append(f"Issue count mismatch: expected {expected_issues}, got {len(issues)}")
                result['passed'] = False

        else:
            result['output'].append("No items found with zero availability")
            result['warnings'].append("Expected to find issues in sample data but found none")
            result['passed'] = False

        result['output'].append("=" * 80)

    except Exception as e:
        result['output'].append(f"✗ Error during tool control processing: {e}")
        result['errors'].append(str(e))
        result['passed'] = False

    # Show expected results
    result['output'].append("")
    result['output'].append("EXPECTED RESULTS FOR SAMPLE DATA:")
    result['output'].append("-" * 80)
    result['output'].append("Should find 5 SEPARATE ROWS with zero availability:")
    result['output'].append("")
    result['output'].append("Row 2:  SEQ 2.1, Part STD-1151, DOWNLOCK PIN SAFETY (Tool)")
    result['output'].append("Row 5:  SEQ 2.2, Part STD-1151, DOWNLOCK PIN SAFETY (Tool)")
    result['output'].append("Row 6:  SEQ 2.2, Part STD-1152, DOWNLOCK PIN SAFETY (Tool)")
    result['output'].append("Row 9:  SEQ 3.1, Part G50463, PAD-FLUID ABSORBENT (Spare)")
    result['output'].append("Row 12: SEQ 4.1, Part STD-1330, WRENCH - HEXDRIVE, ALLEN (Tool)")
    result['output'].append("")
    result['output'].append("KEY POINTS:")
    result['output'].append("  • Rows 2 and 5: Same part (STD-1151), BOTH appear (different rows)")
    result['output'].append("  • Rows 5 and 6: Same SEQ (2.2), BOTH appear (different parts)")
    result['output'].append("  • NO deduplication - each row is independent")
    result['output'].append("-" * 80)

    return result


def create_sample_data():
    """
    Create sample data to test tool control feature.

    Returns:
        pd.DataFrame: Sample data with tool control columns
    """
    data = {
        SEQ_NO_COLUMN: [
            '2.1', '2.1', '2.1',  # Same SEQ, different parts
            '2.2', '2.2', '2.2', '2.2',  # Same SEQ, different parts
            '3.1', '3.1',  # Same SEQ, different parts
            '3.2',  # Single part
            '4.1', '4.1', '4.2'  # Mix
        ],
        TITLE_COLUMN: [
            '21-100-00 (00) / POWER ELECTRONICS COOLING SYSTEM',
            '21-100-00 (00) / POWER ELECTRONICS COOLING SYSTEM',
            '21-100-00 (00) / POWER ELECTRONICS COOLING SYSTEM',
            '21-100-00 (00) / POWER ELECTRONICS COOLING SYSTEM',
            '21-100-00 (00) / POWER ELECTRONICS COOLING SYSTEM',
            '21-100-00 (00) / POWER ELECTRONICS COOLING SYSTEM',
            '21-100-00 (00) / POWER ELECTRONICS COOLING SYSTEM',
            'EO-2024-001 / CABIN AIR SYSTEM',
            'EO-2024-001 / CABIN AIR SYSTEM',
            'EO-2024-002 / BRAKE SYSTEM',
            '24-045-00 / LANDING GEAR',
            '24-045-00 / LANDING GEAR',
            '24-045-00 / LANDING GEAR'
        ],
        TOOL_PARTNO_COLUMN: [
            'STD-1048',  # Has quantity
            'STD-1151',  # Zero - should appear
            'G00270',  # Has quantity
            'STD-1048',  # Has quantity (repeated part)
            'STD-1151',  # Zero - should appear (repeated part, DIFFERENT row)
            'STD-1152',  # Zero - should appear (different part)
            'STD-858',  # Has quantity
            'G00270',  # Has alt quantity
            'G50463',  # Zero - should appear
            'STD-858',  # Has quantity
            'STD-6391',  # Has quantity
            'STD-1330',  # Zero - should appear
            ''  # Empty - should NOT appear
        ],
        TOOL_NAME_COLUMN: [
            'STEPLADDER - 6 FOOT',
            'DOWNLOCK PIN SAFETY',  # Zero - row 2
            'TAPE-WATERPROOF MASK',
            'STEPLADDER - 6 FOOT',
            'DOWNLOCK PIN SAFETY',  # Zero - row 5 (DIFFERENT row, same part)
            'DOWNLOCK PIN SAFETY',  # Zero - row 6 (different part STD-1152!)
            'TAG - DO NOT OPERATE',
            'TAPE-WATERPROOF MASK',
            'PAD-FLUID ABSORBENT',  # Zero - row 9
            'TAG - DO NOT OPERATE',
            'MOP-LONG HANDLE',
            'WRENCH - HEXDRIVE, ALLEN',  # Zero - row 12
            ''
        ],
        TOOL_TYPE_COLUMN: ['Y', 'Y', 'N', 'Y', 'Y', 'Y', 'Y', 'N', 'N', 'Y', 'Y', 'Y', 'Y'],
        TOTAL_QTY_COLUMN: [5, 0, 0, 5, 0, 0, 3, 0, 0, 3, 2, 0, 0],
        ALT_QTY_COLUMN: [0, 0, 2, 0, 0, 0, 1, 2, 0, 1, 0, 0, 0]
    }

    return pd.DataFrame(data)


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING TOOL CONTROL FUNCTIONALITY")
    print("=" * 80)
    print()

    result = test_tool_control()

    for output in result['output']:
        print(output)

    print()

    if result['passed']:
        print("✓ Tool control test PASSED")
    else:
        print("✗ Tool control test FAILED")
        for error in result['errors']:
            print(f"  ERROR: {error}")