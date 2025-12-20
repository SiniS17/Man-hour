# Configuration Guide

## Overview

The Workpack Data Processing System is configured through the `settings.ini` file. This guide explains each configuration section and parameter.

## Configuration File Structure

```ini
[Paths]
[Processing]
[ReferenceSheet]
[UploadedSheet]
[ToolControlColumns]
[SEQ_Mappings]
[SEQ_ID_Mappings]
[Thresholds]
[Output]
```

## Section Details

### [Paths]

Defines folder locations for input, output, reference, and log files.

```ini
[Paths]
input_folder = INPUT
output_folder = OUTPUT
reference_file = B787-Task EO.xlsx
reference_folder = REFERENCE
```

**Parameters:**

- `input_folder`: Location of input Excel files to process
- `output_folder`: Where to save generated reports
- `reference_file`: Name of the file containing task IDs and EO IDs
- `reference_folder`: Location of all reference/lookup files

### [Processing]

Controls processing behavior and features.

```ini
[Processing]
ignore_missing_columns = False
enable_special_code = True
enable_tool_control = True
type_coefficient_per_seq = True
```

**Parameters:**

- `ignore_missing_columns`: Whether to continue if optional columns are missing
- `enable_special_code`: Enable special code distribution analysis
- `enable_tool_control`: Enable tool/spare availability checking
- `type_coefficient_per_seq`: 
  - `True`: Calculate coefficient once per SEQ (deduplicate after coefficient)
  - `False`: Calculate coefficient for every row (like tool control)

### [ReferenceSheet]

Configures reference data files and columns.

#### Task and EO Sheet Configuration

```ini
# Task sheet configuration
task_sheet_name = Task
task_id_column = Taskcard Number

# EO sheet configuration
eo_sheet_name = EO
eo_id_column = EO
eo_prefix = EO
```

**Parameters:**

- `task_sheet_name`: Sheet name in reference file containing task IDs
- `task_id_column`: Column name for task IDs
- `eo_sheet_name`: Sheet name containing EO IDs
- `eo_id_column`: Column name for EO IDs
- `eo_prefix`: Prefix to identify EO IDs (e.g., "EO")

#### Bonus Hours Configuration

```ini
bonus_hours_file = vB20WHourNorm.xlsx
aircraft_code_column = AircraftCode
product_code_column = ProductCode
bonus_1 = Hours
bonus_2 = Hours2
```

**Parameters:**

- `bonus_hours_file`: File containing bonus hours lookup (searches all sheets)
- `aircraft_code_column`: Column for aircraft type matching
- `product_code_column`: Column for check/product type matching
- `bonus_1`: First bonus hours column name
- `bonus_2`: Second bonus hours column name (optional)

**Note**: System sums bonus_1 and bonus_2 if both exist. Only includes rows where `IsActive = TRUE` if that column exists.

#### Aircraft Type Lookup Configuration

```ini
ac_type_file = Regis.xlsx
ac_type_registration_column = Regis
ac_type_type_column = Type
```

**Parameters:**

- `ac_type_file`: File mapping registrations to aircraft types
- `ac_type_registration_column`: Column with aircraft registration/name
- `ac_type_type_column`: Column with aircraft type code

#### Type Coefficient Configuration

```ini
type_coefficient_file = Standard_Work_Coe.xlsx
type_coeff_aircraft_column = AircraftCode
type_coeff_checkgroup_column = CheckGroup
type_coeff_function_column = FuncGroup
type_coeff_column = Coeff
type_coeff_isactive_column = IsActive
```

**Parameters:**

- `type_coefficient_file`: File containing type coefficients (processes all sheets)
- `type_coeff_aircraft_column`: Aircraft code column
- `type_coeff_checkgroup_column`: Check group column (A-CHECK, C-CHECK, etc.)
- `type_coeff_function_column`: Function group column (maps to special_type_column)
- `type_coeff_column`: Coefficient value column
- `type_coeff_isactive_column`: Filter column (only TRUE values included)

#### Check Type Mapping

```ini
check_type_a = A-CHECK
check_type_c = C-CHECK
check_type_y = Y-CHECK
```

**Parameters:**

Maps the first letter of wp_type to check group values. These MUST match the values in the `CheckGroup` column of the type coefficient file.

**Example**: If wp_type is "A06", the system extracts "A" and maps it to "A-CHECK".

### [UploadedSheet]

Defines column names in the input Excel files.

```ini
[UploadedSheet]
seq_no = SEQ
title = forecast.event_display
planned_mhrs = forecast.est_mh
special_code = scl.special
a_column = wph.wpno
special_type_column = special type
```

**Parameters:**

- `seq_no`: Column containing SEQ numbers (e.g., "2.1", "3.45")
- `title`: Column containing task titles/descriptions
- `planned_mhrs`: Column with planned man-hours in MINUTES
- `special_code`: Column for special code analysis (if enabled)
- `a_column`: Column containing aircraft name and wp_type (format: "REGIS-WPTYPE")
- `special_type_column`: Column containing function group for type coefficient lookup

**Important**: 
- The `planned_mhrs` column should contain VALUES IN MINUTES
- The system automatically converts minutes to hours
- If your input is already in hours, modify the conversion function

### [ToolControlColumns]

Defines columns for tool control feature (only used if `enable_tool_control = True`).

```ini
[ToolControlColumns]
tool_name = part.description
tool_type = part.tool
tool_partno = prq2.partno
total_qty = total_qty
alt_qty = altpart_total_qty
```

**Parameters:**

- `tool_name`: Tool or spare part name
- `tool_type`: Type indicator ("Y" = Tool, "N" = Spare)
- `tool_partno`: Part number
- `total_qty`: Total quantity available
- `alt_qty`: Alternative part quantity available

**Logic**: An item shows as having zero availability if BOTH `total_qty = 0` AND `alt_qty = 0`.

### [SEQ_Mappings]

Controls which SEQ prefixes are processed and checked against reference.

```ini
[SEQ_Mappings]
SEQ_2.x = true
SEQ_3.x = true
SEQ_4.x = true
SEQ_5.x = ignore
SEQ_6.x = ignore
```

**Values:**

- `true`: Process and check against reference data
- `false`: Process but don't check against reference
- `ignore`: Completely skip these rows

**Example**: 
- SEQ 2.1, 2.5, 2.39 all use `SEQ_2.x` mapping
- SEQ 3.1, 3.22 all use `SEQ_3.x` mapping

### [SEQ_ID_Mappings]

Defines how to extract task IDs from titles for each SEQ prefix.

```ini
[SEQ_ID_Mappings]
SEQ_2.x_ID = -
SEQ_3.x_ID = -
SEQ_4.x_ID = /
```

**Values:**

- `-`: Extract everything before the first "("
  - Example: "24-045-00 (00) - ITEM 1" → "24-045-00"
- `/`: Extract everything before the first "/"
  - Example: "EO-2024-001 / CABIN AIR" → "EO-2024-001"

### [Thresholds]

Defines various threshold values.

```ini
[Thresholds]
high_mhrs_hours = 16
random_sample_size = 10
```

**Parameters:**

- `high_mhrs_hours`: Tasks with adjusted hours exceeding this appear in "High Man-Hours Tasks" sheet
- `random_sample_size`: Number of random rows to show in debug sample

### [Output]

Controls output formatting and content.

```ini
[Output]
show_bonus_hours_breakdown = True
```

**Parameters:**

- `show_bonus_hours_breakdown`: Show detailed breakdown of bonus hours by source

## Configuration Examples

### Example 1: Different Column Names

If your input files use different column names:

```ini
[UploadedSheet]
seq_no = Sequence_Number
title = Task_Description
planned_mhrs = Estimated_Minutes
special_code = Work_Code
a_column = Aircraft_Info
special_type_column = Work_Category
```

### Example 2: Disable Optional Features

To run without special code or tool control:

```ini
[Processing]
enable_special_code = False
enable_tool_control = False
```

### Example 3: Custom SEQ Processing

To only process SEQ 2.x and 4.x:

```ini
[SEQ_Mappings]
SEQ_2.x = true
SEQ_3.x = ignore
SEQ_4.x = true
SEQ_5.x = ignore
```

## Validation

After editing `settings.ini`, test your configuration:

```bash
python -m tests.test_config
```

This will verify:
- All required settings are present
- Paths exist
- Column mappings are defined
- Values are valid

## Best Practices

1. **Backup Before Changes**: Always backup `settings.ini` before editing
2. **Test Configuration**: Run test suite after changes
3. **Use Descriptive Names**: Keep original column names in comments
4. **Document Custom Settings**: Add comments explaining non-standard values
5. **Version Control**: Track configuration changes in version control

## Troubleshooting Configuration Issues

### Problem: "Column not found" errors

**Solution**: Check that column names in `[UploadedSheet]` exactly match your input files (case-sensitive).

### Problem: Type coefficients not applied

**Solution**: 
1. Verify `special_type_column` exists in input
2. Check that check type mappings match CheckGroup values in coefficient file
3. Ensure aircraft code exists in coefficient file

### Problem: No bonus hours added

**Solution**:
1. Verify aircraft registration is in the aircraft type lookup file
2. Check that product code and aircraft code combination exists in bonus file
3. Ensure `IsActive = TRUE` for relevant rows

## Advanced Configuration

### Multiple Reference Files

The system can work with multiple reference sheets within files:
- Task IDs and EO IDs can be in separate sheets of the same file
- Bonus hours file searches ALL sheets for matches
- Type coefficient file processes ALL sheets

### Dynamic Coefficient Calculation

Set `type_coefficient_per_seq` based on your needs:
- `True`: More like man-hours (one coefficient per unique task)
- `False`: More like tool control (coefficient for every row)

### Custom Ignore Lists

For tool control, create `REFERENCE/ignore_item.txt`:

```
# One item per line
# Can be part number or tool name
STD-1234
COMMON-TOOL-XYZ
# This is a comment
```

Items in this file won't appear in tool control issues.