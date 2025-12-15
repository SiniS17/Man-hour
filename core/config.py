"""
Configuration Module
Loads and manages all configuration settings from settings.ini
"""

import configparser
import os

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
BONUS_HOURS_FILE = config.get('ReferenceSheet', 'bonus_hours_file', fallback='bonus_hours.xlsx')
BONUS_HOURS_SHEET = config.get('ReferenceSheet', 'bonus_hours_sheet', fallback='BonusHours')

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

# SEQ Mappings section - determines how each SEQ prefix should be processed
SEQ_MAPPINGS = {key.upper(): value for key, value in config.items('SEQ_Mappings')}

# SEQ ID Mappings section - determines how to extract ID from title
SEQ_ID_MAPPINGS = {key.upper(): value for key, value in config.items('SEQ_ID_Mappings')}

# SEQ Coefficients section - man-hour multipliers for each SEQ prefix
SEQ_COEFFICIENTS = {}
DEFAULT_COEFFICIENT = 1.0

if config.has_section('SEQ_Coefficients'):
    for key, value in config.items('SEQ_Coefficients'):
        if key == 'default_coefficient':
            DEFAULT_COEFFICIENT = float(value)
        else:
            SEQ_COEFFICIENTS[key.upper()] = float(value)

# Thresholds section
HIGH_MHRS_HOURS = config.getint('Thresholds', 'high_mhrs_hours')
RANDOM_SAMPLE_SIZE = config.getint('Thresholds', 'random_sample_size')


def get_seq_coefficient(seq_no):
    """
    Get the coefficient for a given SEQ number.

    Args:
        seq_no: SEQ identifier (e.g., "2.1", "3.5", "4.2")

    Returns:
        float: Coefficient to multiply man-hours by
    """
    # Extract the major version (e.g., "2" from "2.1")
    seq_prefix = str(seq_no).split('.')[0]

    # Look for the coefficient in the config
    mapping_key = f"SEQ_{seq_prefix}.X"

    if mapping_key in SEQ_COEFFICIENTS:
        return SEQ_COEFFICIENTS[mapping_key]

    return DEFAULT_COEFFICIENT


def print_config():
    """Display the configuration (for debugging purposes)"""
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
    print(f"Bonus Hours Sheet: {BONUS_HOURS_SHEET}")
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
    print(f"SEQ Mappings: {SEQ_MAPPINGS}")
    print(f"SEQ ID Mappings: {SEQ_ID_MAPPINGS}")
    print(f"SEQ Coefficients: {SEQ_COEFFICIENTS}")
    print(f"Default Coefficient: {DEFAULT_COEFFICIENT}")