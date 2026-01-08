"""
Core Package
Contains core business logic for data processing
UPDATED: Removed type coefficient exports
"""

from .config import *
from .data_loader import load_input_files, load_reference_ids
from .id_extractor import extract_task_id, extract_id_from_title
from .data_processor import process_data

__all__ = [
    # Config exports
    'INPUT_FOLDER',
    'OUTPUT_FOLDER',
    'REFERENCE_FILE',
    'REFERENCE_FOLDER',
    'SEQ_NO_COLUMN',
    'TITLE_COLUMN',
    'PLANNED_MHRS_COLUMN',
    'SPECIAL_CODE_COLUMN',
    'ENABLE_SPECIAL_CODE',
    'ENABLE_TOOL_CONTROL',
    'TOOL_NAME_COLUMN',
    'TOOL_TYPE_COLUMN',
    'TOOL_PARTNO_COLUMN',
    'TOTAL_QTY_COLUMN',
    'ALT_QTY_COLUMN',
    'AC_TYPE_FILE',
    'AC_TYPE_REGISTRATION_COLUMN',
    'AC_TYPE_TYPE_COLUMN',
    'BONUS_HOURS_FILE',
    'AIRCRAFT_CODE_COLUMN',
    'PRODUCT_CODE_COLUMN',
    'BONUS_1_COLUMN',
    'BONUS_2_COLUMN',
    'BONUS_ISACTIVE_COLUMN',
    'SHOW_BONUS_HOURS_BREAKDOWN',
    'SEQ_MAPPINGS',
    'SEQ_ID_MAPPINGS',
    'SEQ_COEFFICIENTS',
    'DEFAULT_COEFFICIENT',
    'HIGH_MHRS_HOURS',
    'RANDOM_SAMPLE_SIZE',
    'HOURS_PER_SHIFT',
    'REFERENCE_TASK_SHEET_NAME',
    'REFERENCE_TASK_ID_COLUMN',
    'REFERENCE_EO_SHEET_NAME',
    'REFERENCE_EO_ID_COLUMN',
    'REFERENCE_EO_PREFIX',
    'get_seq_coefficient',
    'print_config',
    'SKIP_COEFFICIENT_CODES',
    'ARRAY_SKIP_COEFFICIENT',

    # Data loader exports
    'load_input_files',
    'load_reference_ids',

    # ID extractor exports
    'extract_task_id',
    'extract_id_from_title',

    # Data processor exports
    'process_data',
]