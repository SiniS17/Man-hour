"""
Configuration Module
Loads and manages all configuration settings from settings.ini
UPDATED: Removed type coefficient, added SEQ coefficient system
"""

import configparser
import os
import pandas as pd

# Load the configuration settings from settings.ini
config = configparser.ConfigParser()

# Ensure the settings.ini file is in the correct directory
config_file_path = os.path.join(os.getcwd(), 'settings.ini')

# Read the settings.ini file
config.read(config_file_path)

# Paths section
INPUT_FOLDER = config['Paths']['input_folder']
OUTPUT_FOLDER = config['Paths']['output_folder']
REFERENCE_FILE = config['Paths']['reference_file']
REFERENCE_FOLDER = config['Paths']['reference_folder']

# Processing section
IGNORE_MISSING_COLUMNS = config.getboolean('Processing', 'ignore_missing_columns')
ENABLE_SPECIAL_CODE = config.getboolean('Processing', 'enable_special_code')
ENABLE_TOOL_CONTROL = config.getboolean('Processing', 'enable_tool_control', fallback=False)

# ReferenceSheet section - Task sheet
REFERENCE_TASK_SHEET_NAME = config['ReferenceSheet']['task_sheet_name']
REFERENCE_TASK_ID_COLUMN = config['ReferenceSheet']['task_id_column']

# ReferenceSheet section - EO sheet
REFERENCE_EO_SHEET_NAME = config['ReferenceSheet']['eo_sheet_name']
REFERENCE_EO_ID_COLUMN = config['ReferenceSheet']['eo_id_column']

# EO prefix for identification
REFERENCE_EO_PREFIX = config['ReferenceSheet']['eo_prefix']

# Bonus hours configuration
BONUS_HOURS_FILE = config.get('ReferenceSheet', 'bonus_hours_file', fallback='vB20WHourNorm.xlsx')
AIRCRAFT_CODE_COLUMN = config.get('ReferenceSheet', 'aircraft_code_column', fallback='Aircraft code')
PRODUCT_CODE_COLUMN = config.get('ReferenceSheet', 'product_code_column', fallback='ProductCode')
BONUS_1_COLUMN = config.get('ReferenceSheet', 'bonus_1', fallback='Hours')
BONUS_2_COLUMN = config.get('ReferenceSheet', 'bonus_2', fallback='Hours2')
BONUS_ISACTIVE_COLUMN = config.get('ReferenceSheet', 'bonus_isactive_column', fallback='IsActive')

# Aircraft type lookup configuration
AC_TYPE_FILE = config.get('ReferenceSheet', 'ac_type_file', fallback='Regis.xlsx')
AC_TYPE_REGISTRATION_COLUMN = config.get('ReferenceSheet', 'ac_type_registration_column', fallback='Regis')
AC_TYPE_TYPE_COLUMN = config.get('ReferenceSheet', 'ac_type_type_column', fallback='Type')

# UploadedSheet section
SEQ_NO_COLUMN = config['UploadedSheet']['seq_no']
TITLE_COLUMN = config['UploadedSheet']['title']
PLANNED_MHRS_COLUMN = config['UploadedSheet']['planned_mhrs']
SPECIAL_CODE_COLUMN = config['UploadedSheet']['special_code']
A_COLUMN = config.get('UploadedSheet', 'a_column', fallback='A')

# Tool Control Columns section
TOOL_NAME_COLUMN = None
TOOL_TYPE_COLUMN = None
TOOL_PARTNO_COLUMN = None
TOTAL_QTY_COLUMN = None
ALT_QTY_COLUMN = None

if config.has_section('ToolControlColumns'):
    TOOL_NAME_COLUMN = config['ToolControlColumns']['tool_name']
    TOOL_TYPE_COLUMN = config['ToolControlColumns']['tool_type']
    TOOL_PARTNO_COLUMN = config['ToolControlColumns']['tool_partno']
    TOTAL_QTY_COLUMN = config['ToolControlColumns']['total_qty']
    ALT_QTY_COLUMN = config['ToolControlColumns']['alt_qty']

# SEQ Mappings section
SEQ_MAPPINGS = {key.upper(): value for key, value in config.items('SEQ_Mappings')}

# SEQ ID Mappings section
SEQ_ID_MAPPINGS = {key.upper(): value for key, value in config.items('SEQ_ID_Mappings')}

# SEQ Coefficients section
SEQ_COEFFICIENTS = {}
DEFAULT_COEFFICIENT = 1.0

if config.has_section('SEQ_Coefficients'):
    for key, value in config.items('SEQ_Coefficients'):
        if key == 'default_coefficient':
            DEFAULT_COEFFICIENT = float(value)
        else:
            SEQ_COEFFICIENTS[key.upper()] = float(value)

# Skip Coefficient section
SKIP_COEFFICIENT_CODES = []
ARRAY_SKIP_COEFFICIENT = 1.0

if config.has_section('SkipCoefficient'):
    # Load the list of task codes to skip
    skip_codes_str = config.get('SkipCoefficient', 'skip_codes', fallback='')
    if skip_codes_str.strip():
        # Parse comma-separated values and strip whitespace
        SKIP_COEFFICIENT_CODES = [code.strip() for code in skip_codes_str.split(',') if code.strip()]

    # Load the coefficient to use for skipped codes
    ARRAY_SKIP_COEFFICIENT = config.getfloat('SkipCoefficient', 'array_skip_coefficient', fallback=1.0)

# Thresholds section
HIGH_MHRS_HOURS = config.getint('Thresholds', 'high_mhrs_hours')
RANDOM_SAMPLE_SIZE = config.getint('Thresholds', 'random_sample_size')
HOURS_PER_SHIFT = config.getint('Thresholds', 'hours_per_shift', fallback=8)

# Output section
SHOW_BONUS_HOURS_BREAKDOWN = config.getboolean('Output', 'show_bonus_hours_breakdown', fallback=True)


def get_seq_coefficient(seq_no, task_id=None):
    """
    Get the coefficient for a given SEQ number.

    Args:
        seq_no: SEQ identifier (e.g., "2.1", "3.5", "4.2")
        task_id: Optional task ID to check against skip list

    Returns:
        float: Coefficient to apply (e.g., 2.0, 1.0)
    """
    # First check if this task code should skip coefficient
    if task_id and SKIP_COEFFICIENT_CODES:
        task_id_str = str(task_id).strip().upper()  # Convert to uppercase
        for skip_code in SKIP_COEFFICIENT_CODES:
            if skip_code.upper() in task_id_str:  # Case-insensitive comparison
                return ARRAY_SKIP_COEFFICIENT

    # Normal coefficient logic
    if pd.isna(seq_no):
        return DEFAULT_COEFFICIENT

    seq_str = str(seq_no)
    seq_prefix = seq_str.split('.')[0]
    mapping_key = f"SEQ_{seq_prefix}.X"

    return SEQ_COEFFICIENTS.get(mapping_key, DEFAULT_COEFFICIENT)


def print_config():
    """
    Display the configuration (for debugging purposes).
    """
    print(f"Input folder: {INPUT_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"Reference file: {REFERENCE_FILE}")
    print(f"Reference folder: {REFERENCE_FOLDER}")
    print(f"Reference Task Sheet Name: {REFERENCE_TASK_SHEET_NAME}")
    print(f"Reference Task ID Column: {REFERENCE_TASK_ID_COLUMN}")
    print(f"Reference EO Sheet Name: {REFERENCE_EO_SHEET_NAME}")
    print(f"Reference EO ID Column: {REFERENCE_EO_ID_COLUMN}")
    print(f"EO Prefix: {REFERENCE_EO_PREFIX}")
    print(f"Bonus Hours File: {BONUS_HOURS_FILE}")
    print(f"Aircraft Code Column: {AIRCRAFT_CODE_COLUMN}")
    print(f"Product Code Column: {PRODUCT_CODE_COLUMN}")
    print(f"Bonus Column 1: {BONUS_1_COLUMN}")
    print(f"Bonus Column 2: {BONUS_2_COLUMN}")
    print(f"Bonus IsActive Column: {BONUS_ISACTIVE_COLUMN}")
    print(f"Aircraft Type File: {AC_TYPE_FILE}")
    print(f"Aircraft Registration Column: {AC_TYPE_REGISTRATION_COLUMN}")
    print(f"Aircraft Type Column: {AC_TYPE_TYPE_COLUMN}")
    print(f"Seq. No. Column: {SEQ_NO_COLUMN}")
    print(f"Title Column: {TITLE_COLUMN}")
    print(f"Planned Mhrs Column: {PLANNED_MHRS_COLUMN}")
    print(f"Special Code Column: {SPECIAL_CODE_COLUMN}")
    print(f"A Column: {A_COLUMN}")
    print(f"Enable Special Code: {ENABLE_SPECIAL_CODE}")
    print(f"Enable Tool Control: {ENABLE_TOOL_CONTROL}")
    if ENABLE_TOOL_CONTROL:
        print(f"Tool Name Column: {TOOL_NAME_COLUMN}")
        print(f"Tool Type Column: {TOOL_TYPE_COLUMN}")
        print(f"Tool Part No Column: {TOOL_PARTNO_COLUMN}")
        print(f"Total Qty Column: {TOTAL_QTY_COLUMN}")
        print(f"Alt Qty Column: {ALT_QTY_COLUMN}")
    print(f"High Mhrs Threshold: {HIGH_MHRS_HOURS}")
    print(f"Random Sample Size: {RANDOM_SAMPLE_SIZE}")
    print(f"Hours per Shift: {HOURS_PER_SHIFT}")
    print(f"Show Bonus Hours Breakdown: {SHOW_BONUS_HOURS_BREAKDOWN}")
    print(f"SEQ Mappings: {SEQ_MAPPINGS}")
    print(f"SEQ ID Mappings: {SEQ_ID_MAPPINGS}")
    print(f"Skip Coefficient Codes: {SKIP_COEFFICIENT_CODES}")
    print(f"SEQ Coefficients: {SEQ_COEFFICIENTS}")
    print(f"Array Skip Coefficient: {ARRAY_SKIP_COEFFICIENT}")
    print(f"Default Coefficient: {DEFAULT_COEFFICIENT}")



