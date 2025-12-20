# Installation and Quick Start Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Initial Setup](#initial-setup)
4. [Quick Start](#quick-start)
5. [Verification](#verification)
6. [Next Steps](#next-steps)

---

## System Requirements

### Minimum Requirements

- **Operating System:** Windows 10, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python:** Version 3.7 or higher
- **RAM:** 4 GB minimum, 8 GB recommended
- **Disk Space:** 500 MB for application, plus space for data files
- **Excel:** Microsoft Office 2007+ (for viewing outputs) or LibreOffice Calc

### Software Dependencies

- Python 3.7+
- pandas (Python library)
- openpyxl (Python library)
- configparser (built-in with Python)

---

## Installation

### Step 1: Check Python Installation

**On Windows:**
```cmd
python --version
```

**On macOS/Linux:**
```bash
python3 --version
```

**Expected output:** `Python 3.7.x` or higher

**If Python is not installed:**
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **macOS:** `brew install python3` or download from python.org
- **Linux:** `sudo apt-get install python3 python3-pip`

### Step 2: Extract the System

1. Extract the ZIP file to your desired location
2. Navigate to the extracted folder

**Example:**
```bash
cd /path/to/workpack-system
```

### Step 3: Install Dependencies

**On Windows:**
```cmd
python -m pip install pandas openpyxl
```

**On macOS/Linux:**
```bash
python3 -m pip install pandas openpyxl
```

**Verify installation:**
```bash
python -c "import pandas; import openpyxl; print('Dependencies installed successfully')"
```

---

## Initial Setup

### Step 1: Understand Folder Structure

```
workpack-system/
├── INPUT/              ← Put your Excel files here
├── OUTPUT/             ← Generated reports appear here
├── LOG/                ← Processing logs saved here
├── REFERENCE/          ← Reference data files
├── core/               ← Core system files (do not modify)
├── features/           ← Feature modules (do not modify)
├── utils/              ← Utility functions (do not modify)
├── writers/            ← Output generators (do not modify)
├── tests/              ← Test modules
├── settings.ini        ← Configuration file (customize this)
├── main.py             ← Main program entry point
└── README.md           ← Documentation
```

### Step 2: Prepare Reference Files

Copy your reference files to the `REFERENCE/` folder:

**Required files:**
1. **Task/EO Reference** (default: `B787-Task EO.xlsx`)
   - Contains task IDs and EO IDs
   - Two sheets: "Task" and "EO"

2. **Bonus Hours** (default: `vB20WHourNorm.xlsx`)
   - Contains bonus hours by aircraft and check type
   - Can have multiple sheets

3. **Aircraft Registration** (default: `Regis.xlsx`)
   - Maps aircraft registration to aircraft type
   - Columns: Regis, Type

4. **Type Coefficients** (default: `Standard_Work_Coe.xlsx`)
   - Contains type coefficients
   - Columns: AircraftCode, CheckGroup, FuncGroup, Coeff, IsActive

**Optional file:**
5. **Ignore List** (`ignore_item.txt`)
   - List of tools/spares to ignore in tool control
   - One item per line

**Example REFERENCE folder:**
```
REFERENCE/
├── B787-Task EO.xlsx
├── vB20WHourNorm.xlsx
├── Regis.xlsx
├── Standard_Work_Coe.xlsx
└── ignore_item.txt
```

### Step 3: Configure the System

1. Open `settings.ini` in a text editor

2. **Verify paths** (usually don't need to change):
```ini
[Paths]
input_folder = INPUT
output_folder = OUTPUT
reference_file = B787-Task EO.xlsx
reference_folder = REFERENCE
```

3. **Update column names** to match your input files:
```ini
[UploadedSheet]
seq_no = SEQ                      ← Column with SEQ numbers
title = forecast.event_display    ← Column with task titles
planned_mhrs = forecast.est_mh    ← Column with man-hours (in MINUTES)
special_code = scl.special        ← Column with special codes
a_column = wph.wpno               ← Column with aircraft info
special_type_column = special type ← Column with function groups
```

4. **Configure features:**
```ini
[Processing]
enable_special_code = True    ← Enable special code analysis
enable_tool_control = True    ← Enable tool availability checking
type_coefficient_per_seq = True ← Type coefficient calculation mode
```

5. **Save the file**

### Step 4: Prepare Input Files

1. Save your workpack Excel files to the `INPUT/` folder
2. Ensure files have `.xlsx` extension (not `.xls`)
3. Verify files contain required columns

**Example INPUT folder:**
```
INPUT/
├── VN-A123-A06_workpack.xlsx
├── VN-A456-C12_workpack.xlsx
└── VN-A789-Y01_workpack.xlsx
```

---

## Quick Start

### Run Your First Processing

1. **Open terminal/command prompt** in the system folder

2. **Run the system:**

**On Windows:**
```cmd
python main.py
```

**On macOS/Linux:**
```bash
python3 main.py
```

3. **Monitor the output:**
```
================================================================================
WORKPACK DATA PROCESSING SYSTEM
================================================================================

Configuration:
--------------------------------------------------------------------------------
Input folder: INPUT
Output folder: OUTPUT
...

Step 1: Loading Input Files
--------------------------------------------------------------------------------
Found 3 Excel file(s) in 'INPUT' folder

Step 2: Loading Reference Data
--------------------------------------------------------------------------------
Loaded 1250 Task IDs from 'Task' sheet
Loaded 89 EO IDs from 'EO' sheet

Step 3: Processing Files
================================================================================

Processing file 1/3: INPUT/VN-A123-A06_workpack.xlsx
--------------------------------------------------------------------------------
...
✓ Successfully processed INPUT/VN-A123-A06_workpack.xlsx

================================================================================
PROCESSING COMPLETE
================================================================================

✓ All 3 file(s) processed successfully!

Output files location:
  - Excel reports: OUTPUT/
  - Processing logs: LOG/
```

4. **Check the outputs:**

**Excel Reports:**
```
OUTPUT/
├── VN-A123-A06_workpack/
│   └── VN-A123-A06_workpack_20250101_143022.xlsx
├── VN-A456-C12_workpack/
│   └── VN-A456-C12_workpack_20250101_143045.xlsx
└── VN-A789-Y01_workpack/
    └── VN-A789-Y01_workpack_20250101_143108.xlsx
```

**Log Files:**
```
LOG/
├── application.log
├── VN-A123-A06_workpack/
│   └── processing_20250101_143022.log
├── VN-A456-C12_workpack/
│   └── processing_20250101_143045.log
└── VN-A789-Y01_workpack/
    └── processing_20250101_143108.log
```

---

## Verification

### Verify Installation

Run the test suite to verify everything is working:

```bash
python -m tests.test_runner
```

**Expected output:**
```
================================================================================
RUNNING COMPREHENSIVE TEST SUITE
================================================================================

Test 1: Configuration Validation
--------------------------------------------------------------------------------
✓ Configuration test completed successfully

Test 2: Coefficient Functionality
--------------------------------------------------------------------------------
✓ Coefficients test completed successfully

Test 3: Tool Control Functionality
--------------------------------------------------------------------------------
✓ Tool Control test completed successfully

Test 4: Data Quality Checks
--------------------------------------------------------------------------------
✓ Data Quality test completed successfully

================================================================================
TEST SUMMARY
================================================================================

✓ Configuration: PASSED
✓ Coefficients: PASSED
✓ Tool Control: PASSED
✓ Data Quality: PASSED

Total Tests: 4
Passed: 4
Failed: 0

✓ ALL TESTS PASSED!
```

### Verify Configuration

```bash
python -m tests.test_config
```

This checks:
- All required settings present
- Paths exist
- Column mappings defined
- Values are valid

### Verify Excel Output

Open one of the generated Excel files and verify it contains:

1. **Total Man-Hours Summary** sheet
   - Project information section
   - Man-hours calculation section
   - Additional hours breakdown
   - Final total

2. **Special Code Distribution** sheet (if enabled)
   - List of special codes with hours
   - Sortable and filterable

3. **High Man-Hours Tasks** sheet
   - Tasks exceeding threshold
   - With coefficients applied

4. **New Task IDs** sheet
   - Task IDs not in reference

5. **Tool Control** sheet (if enabled)
   - Tools/spares with zero availability

---

## Next Steps

### Learn More

After successful installation and first run:

1. **Read the User Guide** for detailed usage instructions
   - [USER_GUIDE.md](USER_GUIDE.md)

2. **Review Configuration Options** to customize behavior
   - [CONFIGURATION.md](CONFIGURATION.md)

3. **Understand Calculations** in the Technical Reference
   - [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md)

### Common First-Time Tasks

#### Task 1: Update Column Names

If you get "Missing required columns" error:

1. Open your input Excel file
2. Note the exact column names
3. Update `settings.ini` → `[UploadedSheet]` section
4. Run again

#### Task 2: Add Your Reference Data

1. Export your reference data to Excel files
2. Format according to expected structure
3. Place in `REFERENCE/` folder
4. Update file names in `settings.ini` if different
5. Run processing

#### Task 3: Customize Output

To change what appears in output:

1. Adjust thresholds in `settings.ini`:
   ```ini
   [Thresholds]
   high_mhrs_hours = 16  ← Change threshold
   random_sample_size = 10 ← Change sample size
   ```

2. Enable/disable features:
   ```ini
   [Processing]
   enable_special_code = False  ← Disable special code
   enable_tool_control = False  ← Disable tool control
   ```

3. Show/hide bonus breakdown:
   ```ini
   [Output]
   show_bonus_hours_breakdown = True
   ```

### Maintenance Tasks

#### Update Reference Data

To update task IDs, bonus hours, or coefficients:

1. Update the relevant file in `REFERENCE/` folder
2. No code changes needed
3. Reprocess files

#### Process New Workpacks

1. Save new Excel files to `INPUT/` folder
2. Run `python main.py`
3. Find outputs in `OUTPUT/` folder

#### Archive Old Data

Periodically clean up:

```bash
# Move old outputs
mkdir ARCHIVE
mv OUTPUT/old_workpack_* ARCHIVE/

# Clean input folder
mv INPUT/*.xlsx PROCESSED/
```

---

## Troubleshooting Installation

### Python Not Found

**Error:** `'python' is not recognized as an internal or external command`

**Solution:** 
1. Install Python from python.org
2. During installation, check "Add Python to PATH"
3. Restart terminal/command prompt

### pip Not Found

**Error:** `'pip' is not recognized`

**Solution:**
```bash
# Windows
python -m ensurepip --upgrade

# macOS/Linux
python3 -m ensurepip --upgrade
```

### Permission Denied

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solutions:**
- Run terminal as administrator (Windows)
- Use `sudo` on macOS/Linux
- Check folder permissions
- Close any open Excel files

### Import Error After Installation

**Error:** `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
# Verify which Python you're using
which python    # macOS/Linux
where python    # Windows

# Install with that specific Python
python -m pip install pandas openpyxl
# or
python3 -m pip install pandas openpyxl
```

---

## Support

If you encounter issues during installation:

1. **Check this guide** for solutions
2. **Run test suite** to identify problems
3. **Check log files** for error messages
4. **Review Troubleshooting Guide** for detailed solutions
5. **Contact support** with:
   - Operating system and version
   - Python version (`python --version`)
   - Error messages
   - Steps you've tried

---

## Summary Checklist

Installation complete when you can check all these:

- [ ] Python 3.7+ installed
- [ ] Dependencies installed (pandas, openpyxl)
- [ ] System extracted to folder
- [ ] Reference files in REFERENCE/ folder
- [ ] settings.ini configured for your columns
- [ ] Test suite passes
- [ ] Successfully processed at least one file
- [ ] Excel output opens correctly
- [ ] Log files created in LOG/ folder

**Congratulations! You're ready to use the Workpack Data Processing System.**

For detailed usage instructions, see the [User Guide](USER_GUIDE.md).