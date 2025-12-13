# Workpack Data Processing System

A modular Python system for processing aircraft workpack data, extracting task IDs, calculating man-hours with coefficients, and generating comprehensive Excel reports.

## 🚀 Quick Start

### 1. Run Tests (Recommended First)
```bash
python run_tests.py
```

This will verify:
- Configuration is correct
- All modules are working
- Sample data processing works
- Results saved to `LOG/tests/`

### 2. Process Your Files
```bash
python main.py
```

This will:
- Load files from `INPUT/` folder
- Process each file
- Generate Excel reports in `OUTPUT/`
- Save debug logs to `LOG/`

---

## 📁 Project Structure

```
project/
├── core/                   # Core business logic
│   ├── config.py          # Configuration management
│   ├── data_loader.py     # File loading operations
│   ├── data_processor.py  # Main processing logic
│   └── id_extractor.py    # Task ID extraction
│
├── features/              # Feature modules
│   ├── tool_control.py    # Tool availability checking
│   ├── special_code.py    # Special code analysis
│   └── coefficients.py    # Coefficient calculations
│
├── writers/               # Output generation
│   ├── excel_writer.py    # Excel orchestration
│   ├── sheet_*.py         # Individual sheet generators
│   └── debug_logger.py    # Debug log generation
│
├── utils/                 # Utility functions
│   ├── time_utils.py      # Time conversions
│   ├── validation.py      # Data validation
│   └── formatters.py      # String formatting
│
├── tests/                 # Test suite
│   ├── test_runner.py     # Test orchestration
│   ├── test_config.py     # Configuration tests
│   ├── test_coefficients.py  # Coefficient tests
│   ├── test_tool_control.py  # Tool control tests
│   └── test_data_quality.py  # Data quality tests
│
├── main.py                # Main entry point
├── run_tests.py           # Quick test runner
├── settings.ini           # Configuration file
│
├── INPUT/                 # Input Excel files
├── OUTPUT/                # Generated reports
├── REFERENCE/             # Reference data files
└── LOG/                   # Debug and test logs
```

---

## ⚙️ Configuration

Edit `settings.ini` to configure:

### Paths
```ini
[Paths]
input_folder = INPUT
output_folder = OUTPUT
reference_file = B787-Task EO.xlsx
reference_folder = REFERENCE
```

### Features
```ini
[Processing]
enable_special_code = True    # Enable special code analysis
enable_tool_control = True    # Enable tool availability checking
```

### SEQ Processing
```ini
[SEQ_Mappings]
SEQ_2.x = true     # Process and check reference
SEQ_3.x = true     # Process and check reference
SEQ_4.x = true     # Process but don't check reference
SEQ_5.x = ignore   # Completely ignore
```

### Coefficients
```ini
[SEQ_Coefficients]
SEQ_2.x = 2.0      # Multiply man-hours by 2.0
SEQ_3.x = 2.0      # Multiply man-hours by 2.0
SEQ_4.x = 1.0      # No multiplication
default_coefficient = 1.0
```

---

## 📊 Output Files

### Excel Reports (OUTPUT/)
Each processed file generates an Excel report with sheets:

1. **Total Man-Hours**
   - Base vs adjusted man-hours
   - Special code distribution
   - Average hours per day
   - Percentage breakdown

2. **High Man-Hours Tasks**
   - Tasks exceeding threshold
   - Coefficient information
   - Base vs adjusted hours

3. **New Task IDs**
   - Task IDs not in reference data
   - SEQ numbers for each

4. **Tool Control** (if enabled)
   - Tools/spares with zero availability
   - Part numbers and types

### Debug Logs (LOG/)
- Detailed processing information
- Random sample of processed rows
- Man-hours calculations
- Coefficient application

### Test Logs (LOG/tests/)
- Comprehensive test results
- Pass/fail status for each test
- Errors and warnings
- Timestamp for each run

---

## 🧪 Testing

### Run All Tests
```bash
python run_tests.py
```

### Run Individual Tests
```python
from tests import test_config, test_coefficients, test_tool_control

# Run specific test
test_config()
test_coefficients()
test_tool_control()
```

### Quick System Check
```python
from main import quick_test
quick_test()
```

---

## 📝 Usage Examples

### Basic Processing
```python
from main import main
main()
```

### Process Single File
```python
from core.data_loader import load_reference_ids
from core.data_processor import process_data
from writers.excel_writer import save_output_file

# Load reference data
reference_data = load_reference_ids()

# Process file
processed_data = process_data('INPUT/myfile.xlsx', reference_data)

# Save output
save_output_file('INPUT/myfile.xlsx', processed_data)
```

### Custom Coefficient Calculation
```python
from core.config import get_seq_coefficient

coeff_2_1 = get_seq_coefficient("2.1")  # Returns 2.0
coeff_4_5 = get_seq_coefficient("4.5")  # Returns 1.0
```

### Time Conversions
```python
from utils.time_utils import hours_to_hhmm, convert_planned_mhrs

# Convert hours to HH:MM format
time_str = hours_to_hhmm(36.5)  # Returns "36:30"

# Convert minutes to hours
hours = convert_planned_mhrs(120)  # Returns 2.0
```

---

## 🔧 Troubleshooting

### No Input Files Found
- Check that `.xlsx` files are in the `INPUT/` folder
- Verify `input_folder` setting in `settings.ini`

### Configuration Errors
- Run `python run_tests.py` to verify configuration
- Check all required columns are configured in `settings.ini`

### Import Errors
- Ensure all packages are in the correct folders
- Check that `__init__.py` files exist in each package

### Tool Control Not Working
- Verify `enable_tool_control = True` in `settings.ini`
- Check that tool control columns are configured
- Verify columns exist in your input files

---

## 📦 Dependencies

- **pandas** - Data manipulation
- **openpyxl** - Excel file handling
- Python 3.7+

Install dependencies:
```bash
pip install pandas openpyxl
```

---

## 🔄 Migration from Old Structure

If you have code importing from old locations:

### Old Code
```python
from config import get_seq_coefficient
from data_processing import process_data
from input_output import save_output_file
```

### New Code
```python
from core.config import get_seq_coefficient
from core.data_processor import process_data
from writers.excel_writer import save_output_file
```

Or use the compatibility layer (temporary):
```python
from legacy_imports import *  # Imports from old locations (deprecated)
```

---

## 📋 Features

### ✅ Man-Hours Calculation
- Converts minutes to hours
- Applies SEQ-based coefficients
- Tracks base vs adjusted hours
- Identifies high man-hours tasks

### ✅ Task ID Management
- Extracts task IDs from titles
- Checks against reference data
- Identifies new task IDs
- Supports EO and Task IDs

### ✅ Special Code Analysis
- Distribution by special code
- Average hours per day
- Percentage breakdown
- Visual reports

### ✅ Tool Control
- Checks tool availability
- Identifies zero-quantity items
- Tracks both tools and spares
- Processes all rows independently

### ✅ Comprehensive Testing
- Configuration validation
- Coefficient calculations
- Tool control logic
- Data quality checks

### ✅ Professional Logging
- Excel reports with multiple sheets
- Debug logs with sample data
- Test results with timestamps
- Structured output

---

## 🤝 Support

For issues or questions:
1. Check `UPGRADE.md` for migration details
2. Run tests: `python run_tests.py`
3. Review test logs in `LOG/tests/`
4. Check debug logs in `LOG/`

---

## 📄 License

[Your License Here]

---

## 👥 Contributors

VAE04028

---

**Last Updated**: December 13, 2024  
**Version**: 2.0 (Modular Architecture)