"""
Data Loader Module
Handles loading input files and reference data
REFACTORED: Now uses centralized logging system
"""

import os
import glob
import pandas as pd
from utils.logger import get_logger
from core.config import (INPUT_FOLDER, REFERENCE_FOLDER, REFERENCE_FILE,
                     REFERENCE_TASK_SHEET_NAME, REFERENCE_TASK_ID_COLUMN,
                     REFERENCE_EO_SHEET_NAME, REFERENCE_EO_ID_COLUMN)

# Get module-specific logger
logger = get_logger(module_name="data_loader")


def load_input_files():
    """
    Load all Excel files from the input folder.

    Returns:
        list: List of paths to input Excel files
    """
    input_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))

    if not input_files:
        logger.warning(f"No .xlsx files found in the '{INPUT_FOLDER}' folder.")
    else:
        logger.info(f"Found {len(input_files)} Excel file(s) in '{INPUT_FOLDER}' folder")

    return input_files


def load_reference_ids():
    """
    Load reference IDs from both Task and EO sheets.

    Returns:
        dict: Dictionary with keys 'task_ids' and 'eo_ids', each containing a set of IDs
    """
    # Construct path to reference file
    reference_file_path = os.path.join(REFERENCE_FOLDER, REFERENCE_FILE)

    # Initialize result dictionary
    result = {
        'task_ids': set(),
        'eo_ids': set()
    }

    # Load Task IDs from the Task sheet
    try:
        task_df = pd.read_excel(reference_file_path, engine='openpyxl', sheet_name=REFERENCE_TASK_SHEET_NAME)

        # Check if the column exists
        if REFERENCE_TASK_ID_COLUMN not in task_df.columns:
            logger.warning(f"Column '{REFERENCE_TASK_ID_COLUMN}' not found in '{REFERENCE_TASK_SHEET_NAME}' sheet.")
            logger.debug(f"Available columns: {list(task_df.columns)}")
        else:
            task_ids = task_df[REFERENCE_TASK_ID_COLUMN].dropna().apply(str).unique()
            result['task_ids'] = set(task_ids)
            logger.info(f"Loaded {len(result['task_ids'])} Task IDs from '{REFERENCE_TASK_SHEET_NAME}' sheet")

    except Exception as e:
        logger.error(f"Error loading Task sheet: {e}")

    # Load EO IDs from the EO sheet
    try:
        eo_df = pd.read_excel(reference_file_path, engine='openpyxl', sheet_name=REFERENCE_EO_SHEET_NAME)

        # Check if the column exists
        if REFERENCE_EO_ID_COLUMN not in eo_df.columns:
            logger.warning(f"Column '{REFERENCE_EO_ID_COLUMN}' not found in '{REFERENCE_EO_SHEET_NAME}' sheet.")
            logger.debug(f"Available columns: {list(eo_df.columns)}")
        else:
            eo_ids = eo_df[REFERENCE_EO_ID_COLUMN].dropna().apply(str).unique()
            result['eo_ids'] = set(eo_ids)
            logger.info(f"Loaded {len(result['eo_ids'])} EO IDs from '{REFERENCE_EO_SHEET_NAME}' sheet")

    except Exception as e:
        logger.error(f"Error loading EO sheet: {e}")

    return result


def load_input_dataframe(file_path):
    """
    Load a single input Excel file into a DataFrame.

    Args:
        file_path (str): Path to the Excel file

    Returns:
        pd.DataFrame: Loaded DataFrame

    Raises:
        Exception: If file cannot be loaded
    """
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        logger.info(f"Loaded {len(df)} rows from {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        raise


def extract_workpack_dates(df):
    """
    Extract start and end dates from the DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame

    Returns:
        dict: Dictionary with 'start_date', 'end_date', and 'workpack_days'
    """
    result = {
        'start_date': None,
        'end_date': None,
        'workpack_days': None
    }

    if 'Start_date' not in df.columns or 'End_date' not in df.columns:
        logger.warning("Start_date and/or End_date columns not found in the file")
        return result

    try:
        start_date = pd.to_datetime(df['Start_date'].iloc[0])
        end_date = pd.to_datetime(df['End_date'].iloc[0])
        workpack_days = (end_date - start_date).days + 1

        result['start_date'] = start_date
        result['end_date'] = end_date
        result['workpack_days'] = workpack_days

        logger.info(
            f"Workpack period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({workpack_days} days)")

    except Exception as e:
        logger.warning(f"Could not parse start/end dates: {e}")

    return result