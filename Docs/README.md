# Workpack Data Processing System

## Overview

The Workpack Data Processing System is a comprehensive Python-based tool designed to analyze aircraft maintenance workpack data. It processes Excel files containing task information, calculates man-hours with various coefficients, tracks tool availability, and generates detailed reports.

## Key Features

- **Automated Man-Hours Calculation**: Processes base hours and applies type coefficients
- **Type Coefficient System**: Applies function-specific coefficients based on aircraft type and check group
- **Bonus Hours Integration**: Adds workpack-level bonus hours from lookup tables
- **Tool Control**: Tracks tools and spares with zero availability
- **Reference Validation**: Identifies new task IDs not in reference database
- **Special Code Analysis**: Distributes man-hours by special code categories
- **Comprehensive Reporting**: Generates multi-sheet Excel reports with detailed breakdowns
- **Centralized Logging**: All processing steps logged to both console and files

## System Requirements

- Python 3.7 or higher
- Required packages:
  - pandas
  - openpyxl
  - configparser (built-in)

## Installation

1. Extract the system to your desired location
2. Install required packages:
   ```bash
   pip install pandas openpyxl
   ```
3. Verify installation by running:
   ```bash
   python main.py
   ```

## Quick Start

1. **Configure the system**: Edit `settings.ini` to match your column names and file locations
2. **Prepare reference files**: Place reference files in the `REFERENCE/` folder
3. **Add input files**: Place workpack Excel files in the `INPUT/` folder
4. **Run the system**:
   ```bash
   python main.py
   ```
5. **Review outputs**:
   - Excel reports: `OUTPUT/[filename]/`
   - Processing logs: `LOG/[filename]/`

## Folder Structure

```
workpack-system/
├── INPUT/              # Place input Excel files here
├── OUTPUT/             # Generated Excel reports
├── LOG/                # Processing logs
├── REFERENCE/          # Reference data files
│   ├── B787-Task EO.xlsx
│   ├── vB20WHourNorm.xlsx
│   ├── Regis.xlsx
│   ├── Standard_Work_Coe.xlsx
│   └── ignore_item.txt
├── core/               # Core processing logic
├── features/           # Feature-specific modules
├── utils/              # Utility functions
├── writers/            # Excel output generation
├── tests/              # Test modules
├── settings.ini        # Configuration file
└── main.py            # Main entry point
```

## Configuration

The system is configured through `settings.ini`. See [Configuration Guide](CONFIGURATION.md) for detailed information.

## Processing Workflow

1. **Load Configuration**: Read settings from `settings.ini`
2. **Load Reference Data**: Load task IDs, EO IDs, and lookup tables
3. **Process Each File**:
   - Extract aircraft info and check type
   - Calculate base hours from planned minutes
   - Apply type coefficients based on special type column
   - Add workpack-level bonus hours
   - Identify new task IDs
   - Check tool availability (if enabled)
4. **Generate Reports**: Create multi-sheet Excel files
5. **Save Logs**: Write detailed processing logs

## Output Files

### Excel Report Sheets

1. **Total Man-Hours Summary**: Project info, base hours, bonus breakdown, final total
2. **Special Code Distribution**: Hours by special code with filtering
3. **High Man-Hours Tasks**: Tasks exceeding threshold
4. **New Task IDs**: Task IDs not found in reference
5. **Tool Control**: Tools/spares with zero availability (if enabled)

### Log Files

- `LOG/application.log`: Main application log
- `LOG/[filename]/processing_[timestamp].log`: Detailed processing log for each file

## Key Concepts

### Type Coefficient System

Type coefficients adjust base hours based on:
- **Aircraft Code**: Specific aircraft type (e.g., "B787-9")
- **Check Group**: Type of maintenance check (A-CHECK, C-CHECK, Y-CHECK)
- **Function Group**: Work category from special type column

The coefficient is applied to EACH row, then rows are deduplicated by SEQ if `type_coefficient_per_seq = True`.

### Bonus Hours vs Type Coefficients

- **Type Coefficients**: Row-level adjustments that multiply base hours
- **Bonus Hours**: Workpack-level additions added ONCE to the final total

### Deduplication Logic

- **Man-Hours Calculation**: Deduplicates by SEQ (keeps first occurrence)
- **Tool Control**: NO deduplication (checks every row independently)

## Common Use Cases

### Processing a Single Workpack

1. Place Excel file in `INPUT/`
2. Run `python main.py`
3. Find results in `OUTPUT/[filename]/`

### Batch Processing Multiple Workpacks

1. Place all Excel files in `INPUT/`
2. Run `python main.py`
3. Each file creates its own output folder

### Updating Reference Data

1. Update files in `REFERENCE/` folder
2. No code changes needed
3. Run processing as normal

### Customizing Calculations

1. Edit `settings.ini` to change coefficients or mappings
2. Modify lookup files in `REFERENCE/`
3. Adjust thresholds and feature flags

## Troubleshooting

### Missing Columns Error

**Problem**: "Missing required columns" error  
**Solution**: Update column names in `[UploadedSheet]` section of `settings.ini`

### No Type Coefficient Applied

**Problem**: All rows show coefficient of 1.0  
**Solution**: 
- Verify `special_type_column` exists in input file
- Check lookup file has matching aircraft code and check group
- Review LOG file for detailed messages

### Tool Control Not Working

**Problem**: Tool control sheet is empty  
**Solution**:
- Set `enable_tool_control = True` in settings.ini
- Verify tool control columns are configured
- Check that input file has tool control columns

### Bonus Hours Not Applied

**Problem**: No bonus hours shown in output  
**Solution**:
- Verify aircraft type lookup is working (check logs)
- Ensure bonus hours file exists and has correct sheet structure
- Check that `IsActive = TRUE` for relevant records

## Testing

Run the test suite to verify system functionality:

```bash
# Run all tests
python -m tests.test_runner

# Run specific test
python -m tests.test_config
python -m tests.test_coefficients
python -m tests.test_tool_control
python -m tests.test_data_quality
```

## Support and Documentation

- [Configuration Guide](CONFIGURATION.md)
- [User Guide](USER_GUIDE.md)
- [Technical Reference](TECHNICAL_REFERENCE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

## Version History

### Current Version: 2.0

Major refactoring with:
- Centralized logging system
- Type coefficient system overhaul
- Improved bonus hours handling
- Enhanced Excel output formatting

## License

Proprietary - Internal Use Only

## Contact

For support or questions, contact VAE04028