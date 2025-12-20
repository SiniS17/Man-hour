# User Guide

## Introduction

This guide provides step-by-step instructions for using the Workpack Data Processing System. It's designed for users who need to process workpack data but may not be familiar with Python or programming.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Preparing Your Data](#preparing-your-data)
3. [Running the System](#running-the-system)
4. [Understanding the Output](#understanding-the-output)
5. [Common Tasks](#common-tasks)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.7 or higher installed
- Basic understanding of Excel files
- Access to reference data files

### First-Time Setup

1. **Install Python packages** (one-time setup):
   ```bash
   pip install pandas openpyxl
   ```

2. **Verify installation**:
   ```bash
   python main.py
   ```
   
   You should see the system start and check for input files.

3. **Prepare reference data**:
   - Copy reference files to the `REFERENCE/` folder
   - Ensure you have:
     - Task/EO reference file (default: `B787-Task EO.xlsx`)
     - Bonus hours file (default: `vB20WHourNorm.xlsx`)
     - Aircraft type lookup (default: `Regis.xlsx`)
     - Type coefficient file (default: `Standard_Work_Coe.xlsx`)

## Preparing Your Data

### Input File Requirements

Your input Excel files must contain these columns (names configurable in `settings.ini`):

**Required Columns:**
- SEQ number (e.g., "2.1", "3.45")
- Task title/description
- Planned man-hours (in minutes)

**Optional Columns:**
- Special code (for distribution analysis)
- Special type (for type coefficient)
- Tool control columns (tool name, type, part number, quantities)

### Input File Format

**Example of expected format:**

| SEQ | forecast.event_display | forecast.est_mh | special type | wph.wpno |
|-----|------------------------|-----------------|--------------|----------|
| 2.1 | 24-045-00 (00) - TASK | 120 | Electrical | VN-A123-A06 |
| 2.2 | 24-046-00 (00) - TASK | 240 | Mechanical | VN-A123-A06 |

**Key Points:**
- SEQ format: "X.Y" where X is major version, Y is minor
- Planned man-hours: **Value in MINUTES** (system converts to hours)
- wph.wpno format: "REGISTRATION-CHECKTYPE" (e.g., "VN-A123-A06")

### Placing Input Files

1. Save your Excel file(s) to the `INPUT/` folder
2. Files must have `.xlsx` extension
3. Multiple files can be processed in one run

## Running the System

### Basic Usage

1. **Open command prompt/terminal** in the system folder

2. **Run the main script**:
   ```bash
   python main.py
   ```

3. **Monitor progress**:
   - The system will display progress messages
   - Processing details are logged to console and files
   - Each file takes a few seconds to process

4. **Check for completion**:
   - Look for "PROCESSING COMPLETE" message
   - Review any warnings or errors

### What Happens During Processing

The system performs these steps for each input file:

1. **Extract Information**:
   - Aircraft registration and type
   - Work package type
   - Start and end dates

2. **Calculate Base Hours**:
   - Converts minutes to hours
   - Deduplicates by SEQ number

3. **Apply Type Coefficients**:
   - Looks up coefficient based on aircraft, check type, and function
   - Multiplies base hours by coefficient

4. **Add Bonus Hours**:
   - Looks up bonus hours for aircraft/check combination
   - Adds to final total (NOT to individual rows)

5. **Perform Checks**:
   - Identify new task IDs not in reference
   - Find high man-hours tasks
   - Check tool availability (if enabled)

6. **Generate Reports**:
   - Creates Excel file with multiple sheets
   - Saves processing log

## Understanding the Output

### Output Folder Structure

```
OUTPUT/
└── [input_filename]/
    └── [input_filename]_YYYYMMDD_HHMMSS.xlsx
```

Each input file gets its own subfolder with timestamped output.

### Excel Report Sheets

#### Sheet 1: Total Man-Hours Summary

**Purpose**: Overview of total man-hours calculation

**Sections**:
1. **Project Information**:
   - Workpack period and duration
   - Aircraft registration and type
   - Check type (WP type)

2. **Man-Hours Calculation**:
   - Base man-hours (from tasks)
   - Shows in both HH:MM and decimal format

3. **Additional Hours Breakdown**:
   - Bonus hours from lookup files (Towing, ERU, etc.)
   - Type coefficient adjustments by function group
   - Each source shown separately with hours

4. **Final Total**:
   - Total man-hours (base + additional)
   - Average man-hours per day

**How to Read**:
- Base hours = sum of task hours after deduplication
- Additional hours = all bonuses and coefficient adjustments
- Final total = base + additional

#### Sheet 2: Special Code Distribution

**Purpose**: Breakdown of hours by special code

**Columns**:
- Special Code
- Hours (HH:MM)
- Hours (Decimal)
- Avg Hours/Day (if dates available)
- Distribution (%)

**Features**:
- Sortable and filterable (use Excel's filter feature)
- Shows percentage of total for each code
- Includes TOTAL row at bottom

**How to Use**:
- Click filter arrows to sort by hours or percentage
- Use to identify which codes consume most hours
- Calculate resource allocation by code

#### Sheet 3: High Man-Hours Tasks

**Purpose**: Tasks exceeding the configured threshold

**Columns**:
- SEQ
- Title
- Task ID
- Type Coefficient
- Base Mhrs (HH:MM)
- Adjusted Mhrs (HH:MM)

**How to Use**:
- Review tasks requiring significant hours
- Verify type coefficients are applied correctly
- Plan resource allocation for high-hour tasks

**Note**: Threshold set in `settings.ini` under `high_mhrs_hours`

#### Sheet 4: New Task IDs

**Purpose**: Task IDs not found in reference database

**Columns**:
- SEQ
- New Task ID

**How to Use**:
- Review new IDs for accuracy
- Add valid IDs to reference database
- Correct any ID extraction issues

**Note**: Only shows IDs from SEQ mappings set to "true"

#### Sheet 5: Tool Control (if enabled)

**Purpose**: Tools/spares with zero availability

**Columns**:
- SEQ
- Task ID
- Part Number
- Tool/Spare Name
- Type (Tool/Spare)

**How to Use**:
- Review items needing procurement
- Plan tool acquisition before workpack
- Identify critical shortages

**Note**: Items in `ignore_item.txt` are excluded

### Log Files

Logs are saved to `LOG/` folder:

```
LOG/
├── application.log                    # Main application log
└── [input_filename]/
    └── processing_YYYYMMDD_HHMMSS.log # Detailed processing log
```

**Log Contents**:
- Configuration loaded
- Files processed
- Calculation details
- Warnings and errors
- Type coefficient applications
- Bonus hours lookups

**When to Check Logs**:
- Unexpected results
- Missing calculations
- Troubleshooting issues
- Verifying processing steps

## Common Tasks

### Task 1: Process a Single Workpack

1. Place Excel file in `INPUT/` folder
2. Run: `python main.py`
3. Find output in `OUTPUT/[filename]/`
4. Review Excel report
5. Check log if needed

### Task 2: Process Multiple Workpacks

1. Place all Excel files in `INPUT/`
2. Run: `python main.py`
3. System processes each file sequentially
4. Each creates separate output folder
5. Review summary at end

### Task 3: Update Reference Data

**Updating Task IDs**:
1. Open reference file (e.g., `B787-Task EO.xlsx`)
2. Add new task IDs to appropriate sheet
3. Save file
4. Reprocess workpacks

**Updating Bonus Hours**:
1. Open bonus hours file (e.g., `vB20WHourNorm.xlsx`)
2. Update hours or add new aircraft/check combinations
3. Set `IsActive = TRUE` for active records
4. Save file

**Updating Type Coefficients**:
1. Open coefficient file (e.g., `Standard_Work_Coe.xlsx`)
2. Add/update coefficients
3. Ensure `IsActive = TRUE` for active records
4. Match CheckGroup values to config
5. Save file

### Task 4: Change Configuration

1. Open `settings.ini` in text editor
2. Modify required settings
3. Save file
4. Test with: `python -m tests.test_config`
5. Process files normally

### Task 5: Add Items to Ignore List

For tool control, to ignore certain items:

1. Create/open `REFERENCE/ignore_item.txt`
2. Add one item per line (part number or tool name)
3. Save file
4. Items will be excluded from tool control sheet

Example `ignore_item.txt`:
```
# Common tools to ignore
STD-COMMON-001
BASIC-TOOL-KIT
# Consumables
CLEANING-CLOTH
```

## Troubleshooting

### Problem: No Files Found

**Symptoms**: "No .xlsx files found in INPUT folder"

**Solutions**:
1. Verify files are in `INPUT/` folder
2. Check file extension is `.xlsx` (not `.xls`)
3. Ensure INPUT folder exists

### Problem: Missing Column Error

**Symptoms**: "Missing required columns"

**Solutions**:
1. Check error message for missing column names
2. Update `[UploadedSheet]` in `settings.ini` to match your file
3. Verify input file has all required columns

### Problem: Type Coefficients Not Applied

**Symptoms**: All tasks show coefficient of 1.0

**Solutions**:
1. Verify `special_type_column` exists in input file
2. Check log file for lookup details
3. Ensure coefficient file has matching:
   - Aircraft code
   - Check group (from wp_type)
   - Function group (from special type column)
4. Verify `IsActive = TRUE` in coefficient file

### Problem: No Bonus Hours Added

**Symptoms**: Additional hours section is empty or only shows type coefficients

**Solutions**:
1. Check log file for aircraft type lookup
2. Verify aircraft registration is in `Regis.xlsx`
3. Ensure bonus file has entry for aircraft type + check type
4. Check `IsActive = TRUE` in bonus file

### Problem: Tool Control Sheet Empty

**Symptoms**: Tool control sheet shows "All tools have adequate availability"

**Solutions**:
1. Verify `enable_tool_control = True` in settings
2. Check tool control columns are configured
3. Ensure input file has tool columns
4. Review if items are in ignore list

### Problem: Incorrect Totals

**Symptoms**: Man-hours don't match expectations

**Diagnostic Steps**:
1. Check log file for calculation details
2. Review "TOTALS CALCULATION" section in log
3. Verify base hours calculation
4. Check type coefficient applications
5. Confirm bonus hours lookup

**Common Causes**:
- Duplicate SEQ numbers (deduplication affects totals)
- Wrong coefficient lookup
- Bonus hours applied incorrectly
- Input data issues

### Problem: Processing is Slow

**Symptoms**: Takes long time to process

**Solutions**:
1. Process files individually
2. Remove old files from INPUT folder
3. Check file size (very large files take longer)
4. Disable unused features in settings

## Tips for Best Results

1. **Consistent File Format**: Use same column structure across files
2. **Clean Data**: Remove empty rows and columns
3. **Verify Dates**: Ensure start/end dates are valid
4. **Check SEQ Format**: Use "X.Y" format consistently
5. **Review Logs**: Check logs for warnings even when processing succeeds
6. **Backup Reference Data**: Keep copies of reference files before updating
7. **Test Configuration**: Use test suite after configuration changes
8. **Archive Outputs**: Move old output folders periodically

## Getting Help

If you encounter issues:

1. **Check log files** in `LOG/` folder for detailed messages
2. **Review this user guide** for common solutions
3. **Run test suite**: `python -m tests.test_runner`
4. **Check configuration**: `python -m tests.test_config`
5. **Contact support** with:
   - Description of issue
   - Input file (if possible)
   - Log files
   - Screenshots of error messages

## Next Steps

After mastering basic usage:

- Read [Configuration Guide](CONFIGURATION.md) for advanced settings
- Review [Technical Reference](TECHNICAL_REFERENCE.md) to understand calculations
- Check [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed diagnostics