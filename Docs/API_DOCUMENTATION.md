# API Documentation

## Overview

This document provides detailed documentation for all public functions and classes in the Workpack Data Processing System.

## Table of Contents

1. [Core Module](#core-module)
2. [Features Module](#features-module)
3. [Utils Module](#utils-module)
4. [Writers Module](#writers-module)
5. [Logger Module](#logger-module)

---

## Core Module

### core.config

Configuration management and access.

#### `get_check_type_from_wp_type(wp_type)`

Extract check type from work package type.

**Parameters:**
- `wp_type` (str): Work package type (e.g., "A06", "C12", "Y01")

**Returns:**
- `str`: Check type (e.g., "A-CHECK", "C-CHECK", "Y-CHECK") or None

**Example:**
```python
from core.config import get_check_type_from_wp_type

check_type = get_check_type_from_wp_type("A06")
# Returns: "A-CHECK"
```

#### `print_config()`

Display current configuration for debugging.

**Parameters:** None

**Returns:** None (prints to console)

**Example:**
```python
from core.config import print_config

print_config()
```

### core.data_loader

#### `load_input_files()`

Load all Excel files from the input folder.

**Parameters:** None

**Returns:**
- `list`: List of paths to input Excel files

**Example:**
```python
from core.data_loader import load_input_files

files = load_input_files()
for file in files:
    print(f"Found: {file}")
```

#### `load_reference_ids()`

Load reference IDs from both Task and EO sheets.

**Parameters:** None

**Returns:**
- `dict`: Dictionary with keys 'task_ids' and 'eo_ids', each containing a set of IDs

**Example:**
```python
from core.data_loader import load_reference_ids

reference_data = load_reference_ids()
print(f"Task IDs: {len(reference_data['task_ids'])}")
print(f"EO IDs: {len(reference_data['eo_ids'])}")
```

#### `load_input_dataframe(file_path)`

Load a single input Excel file into a DataFrame.

**Parameters:**
- `file_path` (str): Path to the Excel file

**Returns:**
- `pd.DataFrame`: Loaded DataFrame

**Raises:**
- `Exception`: If file cannot be loaded

**Example:**
```python
from core.data_loader import load_input_dataframe

df = load_input_dataframe("INPUT/workpack_001.xlsx")
print(f"Loaded {len(df)} rows")
```

#### `extract_workpack_dates(df)`

Extract start and end dates from DataFrame.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame

**Returns:**
- `dict`: Dictionary with 'start_date', 'end_date', and 'workpack_days'

**Example:**
```python
from core.data_loader import extract_workpack_dates

dates = extract_workpack_dates(df)
print(f"Duration: {dates['workpack_days']} days")
```

### core.data_processor

#### `process_data(input_file_path, reference_data)`

Main data processing function.

**Parameters:**
- `input_file_path` (str): Path to the input Excel file
- `reference_data` (dict): Dictionary containing 'task_ids' and 'eo_ids' sets

**Returns:**
- `dict`: Dictionary with structured data for Excel output

**Example:**
```python
from core.data_processor import process_data
from core.data_loader import load_reference_ids

reference_data = load_reference_ids()
result = process_data("INPUT/workpack_001.xlsx", reference_data)

print(f"Total Man-Hours: {result['total_mhrs']:.2f}")
print(f"Base Hours: {result['total_base_mhrs']:.2f}")
```

**Return Dictionary Structure:**
```python
{
    'total_mhrs': float,
    'total_base_mhrs': float,
    'total_additional_hours': float,
    'bonus_breakdown': dict,
    'ac_type': str,
    'ac_name': str,
    'wp_type': str,
    'special_code_distribution': dict,
    'workpack_days': int,
    'start_date': datetime,
    'end_date': datetime,
    'high_mhrs_tasks': pd.DataFrame,
    'new_task_ids_with_seq': pd.DataFrame,
    'tool_control_issues': pd.DataFrame,
    'debug_sample': pd.DataFrame
}
```

### core.id_extractor

#### `extract_task_id(row)`

Extract task ID from a DataFrame row based on SEQ configuration.

**Parameters:**
- `row`: DataFrame row

**Returns:**
- `tuple`: (task_id, should_check_reference, should_process)

**Example:**
```python
from core.id_extractor import extract_task_id

for idx, row in df.iterrows():
    task_id, should_check, should_process = extract_task_id(row)
    print(f"SEQ {row['SEQ']}: Task ID = {task_id}")
```

#### `extract_id_from_title(title, extraction_method)`

Extract ID from title using specified method.

**Parameters:**
- `title` (str): The title string
- `extraction_method` (str): Either "-" or "/"

**Returns:**
- `str`: The extracted ID string

**Examples:**
```python
from core.id_extractor import extract_id_from_title

# Method "-"
id1 = extract_id_from_title("24-045-00 (00) - ITEM 1", "-")
# Returns: "24-045-00"

# Method "/"
id2 = extract_id_from_title("EO-2024-001 / CABIN AIR", "/")
# Returns: "EO-2024-001"
```

---

## Features Module

### features.a_extractor

#### `extract_from_dataframe(df)`

Extract aircraft name, type, and work package type from DataFrame.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame

**Returns:**
- `tuple`: (ac_type, wp_type, ac_name)

**Example:**
```python
from features.a_extractor import extract_from_dataframe

ac_type, wp_type, ac_name = extract_from_dataframe(df)
print(f"Aircraft: {ac_name} ({ac_type})")
print(f"Check: {wp_type}")
```

#### `load_bonus_hours_lookup()`

Load bonus hours from all sheets in the bonus hours file.

**Parameters:** None

**Returns:**
- `dict`: Nested dictionary {wp_type: {ac_type: total_bonus_hours}}

**Example:**
```python
from features.a_extractor import load_bonus_hours_lookup

bonus_lookup = load_bonus_hours_lookup()
if 'A06' in bonus_lookup and 'B787-9' in bonus_lookup['A06']:
    print(f"Bonus: {bonus_lookup['A06']['B787-9']} hours")
```

#### `get_bonus_hours(ac_type, wp_type, bonus_lookup)`

Look up bonus hours for given aircraft type and work package type.

**Parameters:**
- `ac_type` (str): Aircraft type
- `wp_type` (str): Check/product type
- `bonus_lookup` (dict): Dictionary from load_bonus_hours_lookup()

**Returns:**
- `float`: Bonus hours (0.0 if not found)

**Example:**
```python
from features.a_extractor import get_bonus_hours, load_bonus_hours_lookup

bonus_lookup = load_bonus_hours_lookup()
bonus = get_bonus_hours("B787-9", "A06", bonus_lookup)
print(f"Bonus hours: {bonus:.2f}")
```

### features.type_coefficient

#### `load_type_coefficient_lookup()`

Load type coefficients from the coefficient file.

**Parameters:** None

**Returns:**
- `dict`: Nested dictionary {check_group: {aircraft_code: {func_group: coeff}}}

**Example:**
```python
from features.type_coefficient import load_type_coefficient_lookup

coeff_lookup = load_type_coefficient_lookup()
```

#### `get_type_coefficient(aircraft_code, check_group, func_group, coeff_lookup)`

Look up type coefficient.

**Parameters:**
- `aircraft_code` (str): Aircraft code
- `check_group` (str): Check group
- `func_group` (str): Function group
- `coeff_lookup` (dict): Dictionary from load_type_coefficient_lookup()

**Returns:**
- `float`: Coefficient (1.0 if not found)

**Example:**
```python
from features.type_coefficient import get_type_coefficient

coeff = get_type_coefficient("B787-9", "A-CHECK", "Electrical", coeff_lookup)
print(f"Coefficient: {coeff}")
```

#### `apply_type_coefficients(df, ac_type, wp_type, coeff_lookup)`

Apply type coefficients to DataFrame.

**Parameters:**
- `df` (pd.DataFrame): DataFrame with 'Base Hours' column
- `ac_type` (str): Aircraft type
- `wp_type` (str): Work package type
- `coeff_lookup` (dict): Dictionary from load_type_coefficient_lookup()

**Returns:**
- `pd.DataFrame`: Updated DataFrame with 'Type Coefficient' and 'Adjusted Hours' columns

**Example:**
```python
from features.type_coefficient import apply_type_coefficients, load_type_coefficient_lookup

coeff_lookup = load_type_coefficient_lookup()
df = apply_type_coefficients(df, "B787-9", "A06", coeff_lookup)
```

### features.special_code

#### `calculate_special_code_distribution(df)`

Calculate distribution of planned hours by special code.

**Parameters:**
- `df` (pd.DataFrame): DataFrame with special code and adjusted hours

**Returns:**
- `dict`: Sorted dictionary of {special_code: total_hours}

**Example:**
```python
from features.special_code import calculate_special_code_distribution

distribution = calculate_special_code_distribution(df)
for code, hours in distribution.items():
    print(f"{code}: {hours:.2f} hours")
```

#### `calculate_special_code_per_day(special_code_distribution, workpack_days)`

Calculate average hours per day for each special code.

**Parameters:**
- `special_code_distribution` (dict): Dictionary of {special_code: total_hours}
- `workpack_days` (int): Number of days in the workpack

**Returns:**
- `dict`: Dictionary of {special_code: hours_per_day} or None if invalid days

**Example:**
```python
from features.special_code import calculate_special_code_per_day

per_day = calculate_special_code_per_day(distribution, 10)
for code, hours in per_day.items():
    print(f"{code}: {hours:.2f} hours/day")
```

### features.tool_control

#### `process_tool_control(input_file_path, seq_mappings, seq_id_mappings)`

Main function to process tool control independently.

**Parameters:**
- `input_file_path` (str): Path to the input Excel file
- `seq_mappings` (dict): SEQ mapping configuration
- `seq_id_mappings` (dict): SEQ ID extraction configuration

**Returns:**
- `pd.DataFrame`: DataFrame with tool control issues, or empty DataFrame

**Example:**
```python
from features.tool_control import process_tool_control
from core.config import SEQ_MAPPINGS, SEQ_ID_MAPPINGS

issues = process_tool_control("INPUT/workpack.xlsx", SEQ_MAPPINGS, SEQ_ID_MAPPINGS)
print(f"Found {len(issues)} tool/spare issues")
```

---

## Utils Module

### utils.time_utils

#### `hours_to_hhmm(hours)`

Convert hours to HH:MM format.

**Parameters:**
- `hours` (float): Total hours (can be decimal)

**Returns:**
- `str`: Formatted string in HH:MM format

**Examples:**
```python
from utils.time_utils import hours_to_hhmm

time1 = hours_to_hhmm(36.5)  # Returns: "36:30"
time2 = hours_to_hhmm(2.25)  # Returns: "02:15"
```

#### `convert_planned_mhrs(time_val)`

Convert planned man-hours from minutes to hours.

**Parameters:**
- `time_val`: Numeric value in minutes, or string representation

**Returns:**
- `float`: Hours (converted from minutes)

**Examples:**
```python
from utils.time_utils import convert_planned_mhrs

hours1 = convert_planned_mhrs(120)  # Returns: 2.0
hours2 = convert_planned_mhrs(90)   # Returns: 1.5
```

### utils.validation

#### `validate_required_columns(df, required_columns, file_name)`

Validate that all required columns exist in DataFrame.

**Parameters:**
- `df` (pd.DataFrame): DataFrame to validate
- `required_columns` (list): List of required column names
- `file_name` (str): Name of file being validated

**Returns:**
- `tuple`: (bool: is_valid, list: missing_columns)

**Raises:**
- `ValueError`: If any required columns are missing

**Example:**
```python
from utils.validation import validate_required_columns

try:
    validate_required_columns(df, ['SEQ', 'Title', 'Planned Mhrs'], 'workpack.xlsx')
    print("All columns present")
except ValueError as e:
    print(f"Error: {e}")
```

#### `check_column_exists(df, column_name, file_name)`

Check if a single column exists in DataFrame.

**Parameters:**
- `df` (pd.DataFrame): DataFrame to check
- `column_name` (str): Column name to look for
- `file_name` (str): Name of file being checked

**Returns:**
- `bool`: True if column exists, False otherwise

**Example:**
```python
from utils.validation import check_column_exists

if check_column_exists(df, 'Special Code', 'workpack.xlsx'):
    print("Special code column found")
```

### utils.formatters

#### `clean_string(value)`

Clean a string value by removing extra whitespace and handling None/NaN.

**Parameters:**
- `value`: Value to clean (can be str, None, NaN, etc.)

**Returns:**
- `str`: Cleaned string, or empty string if None/NaN

**Examples:**
```python
from utils.formatters import clean_string

clean1 = clean_string("  hello  ")  # Returns: "hello"
clean2 = clean_string(None)         # Returns: ""
```

#### `format_percentage(value, decimal_places)`

Format a decimal value as a percentage string.

**Parameters:**
- `value` (float): Decimal value (e.g., 0.25 for 25%)
- `decimal_places` (int): Number of decimal places to show (default: 1)

**Returns:**
- `str`: Formatted percentage string

**Examples:**
```python
from utils.formatters import format_percentage

pct1 = format_percentage(0.255, 1)  # Returns: "25.5%"
pct2 = format_percentage(0.5, 2)    # Returns: "50.00%"
```

---

## Writers Module

### writers.excel_writer

#### `save_output_file(input_file_name, report_data)`

Save the report data to Excel file.

**Parameters:**
- `input_file_name` (str): Name of the input file
- `report_data` (dict): Dictionary containing all processed data

**Returns:** None

**Side Effects:**
- Creates Excel file in OUTPUT folder
- Creates subfolder for input file

**Example:**
```python
from writers.excel_writer import save_output_file
from core.data_processor import process_data

report_data = process_data("INPUT/workpack.xlsx", reference_data)
save_output_file("INPUT/workpack.xlsx", report_data)
```

### writers.sheet_total_mhrs

#### `create_total_mhrs_sheet(writer, report_data)`

Create Total Man-Hours Summary and Special Code Distribution sheets.

**Parameters:**
- `writer`: pd.ExcelWriter object
- `report_data` (dict): Dictionary containing processed data

**Returns:** None

**Side Effects:**
- Adds "Total Man-Hours Summary" sheet to Excel file
- Adds "Special Code Distribution" sheet if enabled

**Example:**
```python
import pandas as pd
from writers.sheet_total_mhrs import create_total_mhrs_sheet

with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
    create_total_mhrs_sheet(writer, report_data)
```

---

## Logger Module

### utils.logger.WorkpackLogger

Centralized logger singleton for the entire application.

#### `get_file_logger(base_filename, timestamp=None)`

Get a logger for processing a specific file.

**Parameters:**
- `base_filename` (str): Base name of the file being processed
- `timestamp` (str, optional): Timestamp string

**Returns:**
- `logging.Logger`: File-specific logger

**Example:**
```python
from utils.logger import WorkpackLogger

wl = WorkpackLogger()
logger = wl.get_file_logger("workpack_001")
logger.info("Processing started")
```

#### `get_module_logger(module_name)`

Get a logger for a specific module.

**Parameters:**
- `module_name` (str): Name of the module

**Returns:**
- `logging.Logger`: Module-specific logger

**Example:**
```python
from utils.logger import WorkpackLogger

wl = WorkpackLogger()
logger = wl.get_module_logger("type_coefficient")
logger.info("Loading coefficients")
```

### Convenience Functions

#### `get_logger(module_name=None, base_filename=None)`

Get an appropriate logger based on context.

**Parameters:**
- `module_name` (str, optional): Name of the module
- `base_filename` (str, optional): Base filename for file-specific logging

**Returns:**
- `logging.Logger`: Appropriate logger

**Example:**
```python
from utils.logger import get_logger

# Module-specific logging
logger = get_logger(module_name="data_processor")
logger.info("Processing data")

# File-specific logging
logger = get_logger(base_filename="workpack_001")
logger.info("Started processing workpack_001")
```

#### `info(message)`, `debug(message)`, `warning(message)`, `error(message)`, `critical(message)`

Quick logging functions for the main logger.

**Parameters:**
- `message` (str): Message to log

**Returns:** None

**Example:**
```python
from utils.logger import info, warning, error

info("Processing started")
warning("Missing optional column")
error("Failed to load file")
```

---

## Error Handling

All functions that can fail include proper error handling:

```python
try:
    result = process_data(file_path, reference_data)
except FileNotFoundError:
    # Handle missing file
    pass
except ValueError:
    # Handle invalid data
    pass
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
```

## Type Hints

The codebase uses type hints for better code documentation:

```python
def convert_planned_mhrs(time_val: Union[int, float, str]) -> float:
    """Convert minutes to hours"""
    pass

def process_data(input_file_path: str, reference_data: dict) -> dict:
    """Process workpack data"""
    pass
```

## Thread Safety

- Configuration loading is thread-safe (singleton pattern)
- Logger is thread-safe (uses Python's logging module)
- Data processing is NOT thread-safe (uses pandas DataFrames)

## Best Practices

1. **Always use context managers** for file operations
2. **Check return values** before using them
3. **Handle None values** explicitly
4. **Use try-except blocks** for file I/O
5. **Log important operations** for debugging
6. **Validate input data** before processing
7. **Clean up resources** after use

## Examples

### Complete Processing Pipeline

```python
from core.data_loader import load_input_files, load_reference_ids
from core.data_processor import process_data
from writers.excel_writer import save_output_file
from utils.logger import info, error

# Load reference data once
reference_data = load_reference_ids()

# Process all files
input_files = load_input_files()
for file_path in input_files:
    try:
        info(f"Processing {file_path}")
        report_data = process_data(file_path, reference_data)
        save_output_file(file_path, report_data)
        info(f"Completed {file_path}")
    except Exception as e:
        error(f"Failed to process {file_path}: {e}")
```

### Custom Processing

```python
from core.data_loader import load_input_dataframe
from features.type_coefficient import load_type_coefficient_lookup, apply_type_coefficients
from utils.time_utils import convert_planned_mhrs

# Load data
df = load_input_dataframe("INPUT/workpack.xlsx")

# Convert to hours
df['Base Hours'] = df['Planned Mhrs'].apply(convert_planned_mhrs)

# Apply coefficients
coeff_lookup = load_type_coefficient_lookup()
df = apply_type_coefficients(df, "B787-9", "A06", coeff_lookup)

# Calculate total
total = df['Adjusted Hours'].sum()
print(f"Total: {total:.2f} hours")
```