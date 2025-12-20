# Troubleshooting Guide

## Overview

This guide provides detailed solutions for common issues encountered when using the Workpack Data Processing System.

## Table of Contents

1. [Configuration Issues](#configuration-issues)
2. [Data Loading Issues](#data-loading-issues)
3. [Calculation Issues](#calculation-issues)
4. [Type Coefficient Issues](#type-coefficient-issues)
5. [Tool Control Issues](#tool-control-issues)
6. [Output Issues](#output-issues)
7. [Performance Issues](#performance-issues)
8. [Diagnostic Steps](#diagnostic-steps)

---

## Configuration Issues

### Issue: "No module named 'pandas'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Cause:** Required Python packages not installed

**Solution:**
```bash
pip install pandas openpyxl
```

**Verification:**
```bash
python -c "import pandas; print(pandas.__version__)"
python -c "import openpyxl; print(openpyxl.__version__)"
```

### Issue: "settings.ini not found"

**Symptoms:**
```
FileNotFoundError: settings.ini
```

**Cause:** Configuration file missing or script not run from correct directory

**Solution:**
1. Verify `settings.ini` exists in root directory
2. Run script from root directory: `python main.py`
3. Check current directory: `python -c "import os; print(os.getcwd())"`

### Issue: "Column name not found in settings.ini"

**Symptoms:**
```
KeyError: 'seq_no' not found in [UploadedSheet]
```

**Cause:** Missing or misspelled column configuration

**Solution:**
1. Open `settings.ini`
2. Verify `[UploadedSheet]` section exists
3. Add missing column mapping:
   ```ini
   [UploadedSheet]
   seq_no = SEQ
   title = forecast.event_display
   planned_mhrs = forecast.est_mh
   ```

---

## Data Loading Issues

### Issue: "No .xlsx files found in INPUT folder"

**Symptoms:** System reports no files to process

**Solutions:**

**Check 1: File location**
```bash
# Verify files exist
ls INPUT/
```

**Check 2: File extension**
- Ensure files are `.xlsx` not `.xls`
- Convert if needed using Excel: Save As → Excel Workbook (.xlsx)

**Check 3: Folder exists**
```bash
# Create if missing
mkdir INPUT
```

### Issue: "Missing required columns"

**Symptoms:**
```
ValueError: Missing required columns in file.xlsx. Expected: ['SEQ', 'Title'], Missing: ['Title']
```

**Diagnostic Steps:**

1. **Check actual column names:**
```python
import pandas as pd
df = pd.read_excel("INPUT/your_file.xlsx")
print(df.columns.tolist())
```

2. **Update settings.ini:**
```ini
[UploadedSheet]
seq_no = Actual_Column_Name_From_File
title = Another_Actual_Column_Name
```

3. **Check for extra spaces:**
- Column names are case-sensitive
- "Title" ≠ "title" ≠ " Title "

**Common Mistakes:**
- Extra spaces in column names
- Different case (Title vs title)
- Special characters
- Hidden characters

### Issue: "Error loading reference file"

**Symptoms:**
```
FileNotFoundError: REFERENCE/B787-Task EO.xlsx not found
```

**Solutions:**

1. **Verify file exists:**
```bash
ls REFERENCE/
```

2. **Check filename matches settings:**
```ini
[Paths]
reference_file = B787-Task EO.xlsx  # Must match exactly
```

3. **Check sheet names:**
- Open reference file in Excel
- Verify sheet names match configuration:
  ```ini
  [ReferenceSheet]
  task_sheet_name = Task
  eo_sheet_name = EO
  ```

---

## Calculation Issues

### Issue: Incorrect Total Man-Hours

**Symptoms:** Total doesn't match expected value

**Diagnostic Process:**

1. **Check log file** for calculation breakdown:
```
LOG/[filename]/processing_[timestamp].log
```

Look for sections:
- AFTER BASE HOURS CALCULATION
- AFTER TYPE COEFFICIENT APPLICATION
- TOTALS CALCULATION
- FINAL CALCULATION

2. **Verify components:**
```
Total = Base Hours + Type Coefficient Additional + Bonus Hours
```

3. **Common causes:**

**Cause: Duplicate SEQs**
- System deduplicates by SEQ (keeps first occurrence)
- Check for unintended duplicates in input

**Cause: Wrong minute-to-hour conversion**
- Default: input is in MINUTES
- If your input is already in HOURS, calculation will be wrong
- Solution: Modify `convert_planned_mhrs()` function

**Cause: Type coefficient not applied**
- See [Type Coefficient Issues](#type-coefficient-issues)

**Cause: Bonus hours not found**
- Aircraft type lookup failed
- Product code not in bonus file

### Issue: "Base Hours showing as 0"

**Symptoms:** All base hours are 0.00

**Causes & Solutions:**

**Cause 1: Wrong column**
```python
# Check what's in the planned_mhrs column
import pandas as pd
df = pd.read_excel("INPUT/file.xlsx")
print(df['forecast.est_mh'].head())
```

**Cause 2: Non-numeric values**
- Check for text values like "N/A", "TBD"
- Check for special characters
- System converts invalid values to 0

**Solution:**
```python
# Clean data before processing
df['planned_mhrs'] = pd.to_numeric(df['planned_mhrs'], errors='coerce').fillna(0)
```

---

## Type Coefficient Issues

### Issue: All type coefficients are 1.0

**Symptoms:** No coefficient adjustment applied

**Diagnostic Steps:**

1. **Check special_type_column exists in input:**
```python
import pandas as pd
df = pd.read_excel("INPUT/file.xlsx")
print('special type' in df.columns)
```

2. **Check configuration:**
```ini
[UploadedSheet]
special_type_column = special type  # Must match exactly
```

3. **Check coefficient file loaded:**
Look in log for:
```
LOADING TYPE COEFFICIENTS from Standard_Work_Coe.xlsx
✓ Successfully loaded type coefficients
```

4. **Check lookup values match:**

**Aircraft Code:**
```python
# From input file's column A
ac_name = "VN-A123"
# Looks up in Regis.xlsx -> ac_type = "B787-9"
# Searches coefficient file for aircraft_code = "B787-9"
```

**Check Group:**
```python
# From input file's column A
wp_type = "A06"
# Extracts first letter "A"
# Maps to check_type_a in settings
# Searches coefficient file for check_group = "A-CHECK"
```

**Function Group:**
```python
# From input file's special_type_column
func_group = "Electrical"
# Searches coefficient file for func_group = "Electrical"
```

### Issue: Wrong coefficient applied

**Symptoms:** Unexpected coefficient values

**Solution:**

1. **Verify lookup chain:**
   - Aircraft name → Aircraft type (via Regis.xlsx)
   - WP type → Check group (via settings.ini)
   - Special type → Function group (direct match)

2. **Check coefficient file has all three:**
   ```
   AircraftCode | CheckGroup | FuncGroup   | Coeff
   B787-9       | A-CHECK    | Electrical  | 1.2
   ```

3. **Check IsActive = TRUE:**
   - System only uses rows where IsActive = TRUE
   - Check all relevant rows are active

### Issue: "Could not determine check group"

**Symptoms:**
```
WARNING: Could not determine check group from wp_type 'XYZ'
```

**Cause:** wp_type doesn't start with A, C, or Y

**Solution:**

1. **Update check type mappings:**
```ini
[ReferenceSheet]
check_type_x = X-CHECK  # Add new check type
```

2. **Update code in config.py:**
```python
def get_check_type_from_wp_type(wp_type):
    first_letter = str(wp_type)[0].upper()
    
    if first_letter == 'A':
        return CHECK_TYPE_A
    elif first_letter == 'C':
        return CHECK_TYPE_C
    elif first_letter == 'Y':
        return CHECK_TYPE_Y
    elif first_letter == 'X':  # Add new
        return CHECK_TYPE_X
    else:
        return None
```

---

## Tool Control Issues

### Issue: Tool control sheet is empty

**Symptoms:** "All tools and spares have adequate availability"

**Diagnostic Steps:**

1. **Check feature is enabled:**
```ini
[Processing]
enable_tool_control = True
```

2. **Check columns configured:**
```ini
[ToolControlColumns]
tool_name = part.description
tool_type = part.tool
tool_partno = prq2.partno
total_qty = total_qty
alt_qty = altpart_total_qty
```

3. **Check columns exist in input file:**
```python
import pandas as pd
df = pd.read_excel("INPUT/file.xlsx")
print('part.description' in df.columns)
print('total_qty' in df.columns)
```

4. **Check for zero-quantity items:**
```python
# Items with zero availability:
zero_items = df[(df['total_qty'] == 0) & (df['altpart_total_qty'] == 0)]
print(f"Found {len(zero_items)} items with zero qty")
```

5. **Check ignore list:**
```bash
cat REFERENCE/ignore_item.txt
```
Items in this file won't appear in tool control output.

### Issue: Too many items in tool control

**Symptoms:** Hundreds of items flagged

**Causes:**

1. **Normal items included** (should be in ignore list)
2. **Blank values treated as zero**
3. **Data quality issues** in source

**Solution: Create/update ignore list**

```bash
# REFERENCE/ignore_item.txt
# Common items to ignore
STD-COMMON-TOOL
BASIC-KIT
SAFETY-EQUIPMENT
# Consumables
CLEANING-SUPPLIES
RAGS
TOWELS
```

---

## Output Issues

### Issue: Excel file won't open

**Symptoms:** "File is corrupted" error

**Solutions:**

**Check 1: File was created**
```bash
ls -lh OUTPUT/*/
```

**Check 2: Python errors during generation**
- Check console output for errors
- Check log file for Excel generation errors

**Check 3: File size**
- If 0 bytes, generation failed
- Check for write permissions

**Check 4: Excel version**
- Requires Excel 2007 or later (.xlsx format)
- Try opening with LibreOffice/Google Sheets

### Issue: Missing sheets in Excel file

**Symptoms:** Expected 5 sheets, only see 3

**Solution:**

**Check feature flags:**
```ini
[Processing]
enable_special_code = True   # For special code distribution sheet
enable_tool_control = True   # For tool control sheet
```

**Check log for sheet generation:**
Look for messages like:
```
Creating Total Man-Hours Summary sheet
Creating Special Code Distribution sheet
Creating Tool Control sheet
```

### Issue: Data in wrong columns

**Symptoms:** Column headers don't match data

**Cause:** Column width auto-adjustment failed

**Solution:**
1. Open Excel file
2. Select all: Ctrl+A
3. Auto-fit columns: Double-click column border
4. Save

---

## Performance Issues

### Issue: Processing is very slow

**Symptoms:** Takes minutes to process single file

**Diagnostic Steps:**

1. **Check file size:**
```bash
ls -lh INPUT/*.xlsx
```
Large files (>10MB, >100k rows) take longer

2. **Check enabled features:**
```ini
[Processing]
# Disable unused features
enable_special_code = False
enable_tool_control = False
```

3. **Check lookup file sizes:**
```bash
ls -lh REFERENCE/*.xlsx
```
Large lookup files slow down processing

**Solutions:**

1. **Process files individually** instead of batch
2. **Disable unused features** in settings
3. **Optimize lookup files:**
   - Remove inactive records
   - Keep only necessary columns
   - Use IsActive filter

4. **Split large files** into smaller chunks

### Issue: Out of memory error

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Cause:** File too large for available memory

**Solution:**

1. **Process files individually**
2. **Increase system memory**
3. **Split large files:**
   - Process by date range
   - Process by SEQ range
4. **Close other applications** during processing

---

## Diagnostic Steps

### Step 1: Run Test Suite

```bash
python -m tests.test_runner
```

This checks:
- Configuration valid
- All imports working
- Core functionality working

### Step 2: Check Configuration

```bash
python -m tests.test_config
```

Verifies:
- All settings present
- Paths exist
- Column mappings defined

### Step 3: Enable Debug Logging

Temporarily set all logging to DEBUG level:

```python
# In main.py, add at top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Step 4: Check Log Files

**Main application log:**
```bash
cat LOG/application.log
```

**File-specific log:**
```bash
cat LOG/[filename]/processing_[timestamp].log
```

**Look for:**
- ERROR messages
- WARNING messages
- Unexpected values
- Failed lookups

### Step 5: Validate Input Data

```python
import pandas as pd

# Load file
df = pd.read_excel("INPUT/file.xlsx")

# Check structure
print(f"Rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst row:")
print(df.iloc[0])

# Check for issues
print(f"\nNull values:")
print(df.isnull().sum())

print(f"\nDuplicate SEQs:")
print(df[df.duplicated(subset=['SEQ'], keep=False)])
```

### Step 6: Test Lookups Manually

```python
from features.a_extractor import load_bonus_hours_lookup
from features.type_coefficient import load_type_coefficient_lookup

# Test bonus lookup
bonus = load_bonus_hours_lookup()
print(f"Loaded {len(bonus)} WP types")
print(f"Example: {bonus.get('A06', {})}")

# Test coefficient lookup
coeff = load_type_coefficient_lookup()
print(f"Loaded {len(coeff)} check groups")
```

## Getting Additional Help

If issues persist after following this guide:

1. **Collect diagnostic information:**
   - Input file (if possible to share)
   - Configuration file (settings.ini)
   - Log files from LOG/ folder
   - Screenshots of errors
   - Steps to reproduce

2. **Check for known issues:**
   - Review this troubleshooting guide
   - Check user guide for correct usage
   - Review technical reference

3. **Contact support** with collected information

## Common Error Messages

### "Permission denied"

**Cause:** File is open in Excel or no write permissions

**Solution:**
- Close Excel
- Check folder permissions
- Run as administrator if needed

### "Sheet not found"

**Cause:** Reference file missing expected sheet

**Solution:**
- Check sheet names in reference file
- Update settings.ini to match actual sheet names

### "Invalid configuration"

**Cause:** Syntax error in settings.ini

**Solution:**
- Check for typos
- Ensure proper INI format
- Use `python -m tests.test_config` to validate

### "Unsupported Excel file"

**Cause:** File is .xls (old format) not .xlsx

**Solution:**
- Convert file: Open in Excel → Save As → Excel Workbook (.xlsx)

## Prevention Tips

1. **Validate data before processing:**
   - Check for duplicate SEQs
   - Verify column names
   - Check for null values

2. **Test with small sample first:**
   - Process 1 file before batch
   - Verify results correct
   - Then process remaining files

3. **Keep backups:**
   - Backup settings.ini before changes
   - Backup reference files before updates
   - Archive old outputs

4. **Monitor logs:**
   - Check for warnings
   - Review calculation details
   - Verify lookups successful

5. **Update regularly:**
   - Keep reference data current
   - Test after updates
   - Document customizations