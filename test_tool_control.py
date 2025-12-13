"""
Test script to verify Tool Control functionality (Separate Module)
"""
import pandas as pd
from config import (ENABLE_TOOL_CONTROL, TOOL_NAME_COLUMN, TOOL_TYPE_COLUMN,
                    TOOL_PARTNO_COLUMN, TOTAL_QTY_COLUMN, ALT_QTY_COLUMN,
                    SEQ_NO_COLUMN, TITLE_COLUMN, SEQ_MAPPINGS, SEQ_ID_MAPPINGS)

if ENABLE_TOOL_CONTROL:
    from tool_control import check_tool_availability, get_tool_control_summary


def create_sample_data():
    """Create sample data to test tool control feature - simulating real scenario"""

    # Sample data matching your screenshot scenario
    # Same SEQ can have MULTIPLE different tools/parts - ALL should be checked
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


def test_tool_control():
    """Test the tool control checking logic"""

    print("=" * 80)
    print("TESTING TOOL CONTROL FUNCTIONALITY")
    print("=" * 80)
    print()

    # Check if tool control is enabled
    print(f"Tool Control Enabled: {ENABLE_TOOL_CONTROL}")
    print(f"Tool Name Column: {TOOL_NAME_COLUMN}")
    print(f"Tool Type Column: {TOOL_TYPE_COLUMN}")
    print(f"Tool Part No Column: {TOOL_PARTNO_COLUMN}")
    print(f"Total Qty Column: {TOTAL_QTY_COLUMN}")
    print(f"Alt Qty Column: {ALT_QTY_COLUMN}")
    print()

    if not ENABLE_TOOL_CONTROL:
        print("WARNING: Tool control is disabled in settings.ini")
        print("Set 'enable_tool_control = True' in [Processing] section to enable")
        return

    # Create sample data
    print("Creating sample test data...")
    df = create_sample_data()

    print("\nSample Data:")
    print("-" * 80)
    print(df.to_string(index=False))
    print("-" * 80)
    print()

    # Apply the tool control logic using the separate module
    print("Applying Tool Control Logic (Separate Module)...")
    print("Processing EVERY row independently - NO deduplication")
    print()

    # Use the tool_control module
    result = check_tool_availability(df, SEQ_MAPPINGS, SEQ_ID_MAPPINGS)

    print("RESULTS - Items with ZERO availability (NO DEDUPLICATION):")
    print("=" * 90)

    if len(result) > 0:
        print(result.to_string(index=True))
        print("=" * 90)

        # Get summary
        summary = get_tool_control_summary(result)
        print(f"\nSummary:")
        print(f"  Total issues found: {summary['total_issues']}")
        print(f"  - Tools: {summary['total_tools']}")
        print(f"  - Spares: {summary['total_spares']}")
        print(f"  Unique part numbers: {summary['unique_parts']}")
        print(f"  Affected SEQs: {summary['affected_seqs']}")
    else:
        print("No items found with zero availability")
        print("All tools and spares have adequate stock!")

    print("=" * 90)
    print()

    # Show expected results
    print("\nEXPECTED RESULTS FOR SAMPLE DATA:")
    print("-" * 90)
    print("Should find 5 SEPARATE ROWS with zero availability (NO deduplication):")
    print()
    print("Row 2:  SEQ 2.1, Part STD-1151, DOWNLOCK PIN SAFETY (Tool)")
    print("Row 5:  SEQ 2.2, Part STD-1151, DOWNLOCK PIN SAFETY (Tool) - DIFFERENT row from #2")
    print("Row 6:  SEQ 2.2, Part STD-1152, DOWNLOCK PIN SAFETY (Tool) - DIFFERENT part number")
    print("Row 9:  SEQ 3.1, Part G50463, PAD-FLUID ABSORBENT (Spare)")
    print("Row 12: SEQ 4.1, Part STD-1330, WRENCH - HEXDRIVE, ALLEN (Tool)")
    print()
    print("KEY POINTS:")
    print("  • Row 2 and Row 5: Same part (STD-1151), BOTH should appear (different rows)")
    print("  • Row 5 and Row 6: Same SEQ (2.2), BOTH should appear (different parts)")
    print("  • NO deduplication - each row is independent")
    print("  • Even if same SEQ + same part, if they're different rows, BOTH appear")
    print()
    print("Should NOT include:")
    print("  - Rows with quantity > 0 in either column")
    print("  - Rows with empty part number or tool name")
    print("-" * 90)
    print()


if __name__ == "__main__":
    test_tool_control()
    print("\nTest complete!")
    print("If the results match expected output, tool control is working correctly.")
    print("You can now run main.py to process your actual data files.\n")