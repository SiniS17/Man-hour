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

# ReferenceSheet section
REFERENCE_SHEET_NAME = config['ReferenceSheet']['sheet_name']
REFERENCE_ID_COLUMN = config['ReferenceSheet']['id_column']

# UploadedSheet section
SEQ_NO_COLUMN = config['UploadedSheet']['seq_no']
TITLE_COLUMN = config['UploadedSheet']['title']
PLANNED_MHRS_COLUMN = config['UploadedSheet']['planned_mhrs']
SPECIAL_CODE_COLUMN = config['UploadedSheet']['special_code']

# SEQ Mappings section - determines how each SEQ prefix should be processed
SEQ_MAPPINGS = {key.upper(): value for key, value in config.items('SEQ_Mappings')}

# SEQ ID Mappings section - determines how to extract ID from title
SEQ_ID_MAPPINGS = {key.upper(): value for key, value in config.items('SEQ_ID_Mappings')}

# Thresholds section
HIGH_MHRS_HOURS = config.getint('Thresholds', 'high_mhrs_hours')
RANDOM_SAMPLE_SIZE = config.getint('Thresholds', 'random_sample_size')

# Display the configuration (for debugging purposes)
def print_config():
    print(f"Input folder: {INPUT_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"Reference file: {REFERENCE_FILE}")
    print(f"Reference Sheet Name: {REFERENCE_SHEET_NAME}")
    print(f"Reference ID Column: {REFERENCE_ID_COLUMN}")
    print(f"Seq. No. Column: {SEQ_NO_COLUMN}")
    print(f"Title Column: {TITLE_COLUMN}")
    print(f"Planned Mhrs Column: {PLANNED_MHRS_COLUMN}")
    print(f"Special Code Column: {SPECIAL_CODE_COLUMN}")
    print(f"Enable Special Code: {ENABLE_SPECIAL_CODE}")
    print(f"High Mhrs Threshold: {HIGH_MHRS_HOURS}")
    print(f"Random Sample Size: {RANDOM_SAMPLE_SIZE}")
    print(f"SEQ Mappings: {SEQ_MAPPINGS}")
    print(f"SEQ ID Mappings: {SEQ_ID_MAPPINGS}")