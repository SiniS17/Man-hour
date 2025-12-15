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
TYPE_COEFFICIENT_PER_SEQ = config.getboolean('Processing', 'type_coefficient_per_seq', fallback=True)

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

# Aircraft type lookup configuration
AC_TYPE_FILE = config.get('ReferenceSheet', 'ac_type_file', fallback='Regis.xlsx')
AC_TYPE_REGISTRATION_COLUMN = config.get('ReferenceSheet', 'ac_type_registration_column', fallback='Regis')
AC_TYPE_TYPE_COLUMN = config.get('ReferenceSheet', 'ac_type_type_column', fallback='Type')

# Type coefficient configuration
TYPE_COEFFICIENT_FILE = config.get('ReferenceSheet', 'type_coefficient_file', fallback='Standard_Work_Coe.xlsx')
TYPE_COEFF_FUNCTION_COLUMN = config.get('ReferenceSheet', 'type_coeff_function_column', fallback='Function')
TYPE_COEFF_COLUMN = config.get('ReferenceSheet', 'type_coeff_column', fallback='Coeff')

# Check type mapping (first letter of wp_type -> check type)
CHECK_TYPE_A = config.get('ReferenceSheet', 'check_type_a', fallback='A-check')
CHECK_TYPE_C = config.get('ReferenceSheet', 'check_type_c', fallback='C-check')
CHECK_TYPE_Y = config.get('ReferenceSheet', 'check_type_y', fallback='Y-check')

# UploadedSheet section
SEQ_NO_COLUMN = config['UploadedSheet']['seq_no']
TITLE_COLUMN = config['UploadedSheet']['title']
PLANNED_MHRS_COLUMN = config['UploadedSheet']['planned_mhrs']
SPECIAL_CODE_COLUMN = config['UploadedSheet']['special_code']
A_COLUMN = config.get('UploadedSheet', 'a_column', fallback='A')
SPECIAL_TYPE_COLUMN = config.get('UploadedSheet', 'special_type_column', fallback='special type')

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

# Thresholds section
HIGH_MHRS_HOURS = config.getint('Thresholds', 'high_mhrs_hours')
RANDOM_SAMPLE_SIZE = config.getint('Thresholds', 'random_sample_size')

# Output section
SHOW_BONUS_HOURS_BREAKDOWN = config.getboolean('Output', 'show_bonus_hours_breakdown', fallback=True)


def get_check_type_from_wp_type(wp_type):
    """
    Extract check type from wp_type by looking at first letter.

    Args:
        wp_type: Work package type (e.g., "A06", "C12", "Y01")

    Returns:
        str: Check type (e.g., "A-check", "C-check", "Y-check")

    Examples:
        >>> get_check_type_from_wp_type("A06")
        'A-check'
        >>> get_check_type_from_wp_type("C12")
        'C-check'
    """
    if not wp_type:
        return None

    first_letter = str(wp_type)[0].upper()

    if first_letter == 'A':
        return CHECK_TYPE_A
    elif first_letter == 'C':
        return CHECK_TYPE_C
    elif first_letter == 'Y':
        return CHECK_TYPE_Y
    else:
        return None


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
    print(f"Aircraft Code Column: {AIRCRAFT_CODE_COLUMN}")
    print(f"Product Code Column: {PRODUCT_CODE_COLUMN}")
    print(f"Bonus Column 1: {BONUS_1_COLUMN}")
    print(f"Bonus Column 2: {BONUS_2_COLUMN}")
    print(f"Aircraft Type File: {AC_TYPE_FILE}")
    print(f"Aircraft Registration Column: {AC_TYPE_REGISTRATION_COLUMN}")
    print(f"Aircraft Type Column: {AC_TYPE_TYPE_COLUMN}")
    print(f"Type Coefficient File: {TYPE_COEFFICIENT_FILE}")
    print(f"Type Coeff Function Column: {TYPE_COEFF_FUNCTION_COLUMN}")
    print(f"Type Coefficient Column: {TYPE_COEFF_COLUMN}")
    print(f"Check Type A: {CHECK_TYPE_A}")
    print(f"Check Type C: {CHECK_TYPE_C}")
    print(f"Check Type Y: {CHECK_TYPE_Y}")
    print(f"Type Coefficient Per SEQ: {TYPE_COEFFICIENT_PER_SEQ}")
    print(f"Seq. No. Column: {SEQ_NO_COLUMN}")
    print(f"Title Column: {TITLE_COLUMN}")
    print(f"Planned Mhrs Column: {PLANNED_MHRS_COLUMN}")
    print(f"Special Code Column: {SPECIAL_CODE_COLUMN}")
    print(f"Special Type Column: {SPECIAL_TYPE_COLUMN}")
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
    print(f"Show Bonus Hours Breakdown: {SHOW_BONUS_HOURS_BREAKDOWN}")
    print(f"SEQ Mappings: {SEQ_MAPPINGS}")
    print(f"SEQ ID Mappings: {SEQ_ID_MAPPINGS}")