"""
Centralized Logging System
Provides a unified logging interface for the entire application
"""

import logging
import os
from datetime import datetime
from pathlib import Path


class WorkpackLogger:
    """
    Centralized logger for the workpack processing system.
    Provides both file and console logging with different levels.
    """

    _instance = None
    _loggers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WorkpackLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._setup_logging()

    def _setup_logging(self):
        """Setup the logging configuration"""
        # Create LOG directory
        self.log_dir = Path(os.getcwd()) / 'LOG'
        self.log_dir.mkdir(exist_ok=True)

        # Create main application logger
        self.main_logger = self._create_logger(
            'workpack_main',
            self.log_dir / 'application.log',
            level=logging.INFO
        )

    def _create_logger(self, name, log_file, level=logging.INFO):
        """
        Create a logger with both file and console handlers

        Args:
            name: Logger name
            log_file: Path to log file
            level: Logging level

        Returns:
            logging.Logger: Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        logger.handlers = []

        # File handler - detailed logging
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler - less detailed
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def get_file_logger(self, base_filename, timestamp=None):
        """
        Get a logger for processing a specific file

        Args:
            base_filename: Base name of the file being processed
            timestamp: Optional timestamp string

        Returns:
            logging.Logger: File-specific logger
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger_name = f"workpack_{base_filename}"

        # Return existing logger if available
        if logger_name in self._loggers:
            return self._loggers[logger_name]

        # Create file-specific log directory
        file_log_dir = self.log_dir / base_filename
        file_log_dir.mkdir(exist_ok=True)

        # Create logger with detailed file logging
        log_file = file_log_dir / f"processing_{timestamp}.log"
        logger = self._create_logger(
            logger_name,
            log_file,
            level=logging.DEBUG
        )

        self._loggers[logger_name] = logger
        return logger

    def get_module_logger(self, module_name):
        """
        Get a logger for a specific module

        Args:
            module_name: Name of the module

        Returns:
            logging.Logger: Module-specific logger
        """
        return logging.getLogger(f"workpack.{module_name}")

    @staticmethod
    def info(message, **kwargs):
        """Log info message to main logger"""
        logger = logging.getLogger('workpack_main')
        logger.info(message, **kwargs)

    @staticmethod
    def debug(message, **kwargs):
        """Log debug message to main logger"""
        logger = logging.getLogger('workpack_main')
        logger.debug(message, **kwargs)

    @staticmethod
    def warning(message, **kwargs):
        """Log warning message to main logger"""
        logger = logging.getLogger('workpack_main')
        logger.warning(message, **kwargs)

    @staticmethod
    def error(message, **kwargs):
        """Log error message to main logger"""
        logger = logging.getLogger('workpack_main')
        logger.error(message, **kwargs)

    @staticmethod
    def critical(message, **kwargs):
        """Log critical message to main logger"""
        logger = logging.getLogger('workpack_main')
        logger.critical(message, **kwargs)

    def log_separator(self, logger=None, char="=", length=80):
        """Log a separator line"""
        if logger is None:
            logger = self.main_logger
        logger.info(char * length)

    def log_header(self, title, logger=None):
        """Log a formatted header"""
        if logger is None:
            logger = self.main_logger
        self.log_separator(logger)
        logger.info(title)
        self.log_separator(logger)

    def close_file_logger(self, base_filename):
        """Close and remove a file-specific logger"""
        logger_name = f"workpack_{base_filename}"
        if logger_name in self._loggers:
            logger = self._loggers[logger_name]
            # Close all handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            del self._loggers[logger_name]


# Convenience functions for quick logging
def get_logger(module_name=None, base_filename=None):
    """
    Get an appropriate logger based on context

    Args:
        module_name: Name of the module (for module-specific logging)
        base_filename: Base filename (for file-specific logging)

    Returns:
        logging.Logger: Appropriate logger
    """
    wl = WorkpackLogger()

    if base_filename:
        return wl.get_file_logger(base_filename)
    elif module_name:
        return wl.get_module_logger(module_name)
    else:
        return wl.main_logger


def info(message):
    """Quick info logging"""
    WorkpackLogger.info(message)


def debug(message):
    """Quick debug logging"""
    WorkpackLogger.debug(message)


def warning(message):
    """Quick warning logging"""
    WorkpackLogger.warning(message)


def error(message):
    """Quick error logging"""
    WorkpackLogger.error(message)


def critical(message):
    """Quick critical logging"""
    WorkpackLogger.critical(message)


# Example usage in different contexts:
"""
# In main.py:
from utils.logger import WorkpackLogger, info, error

info("Starting workpack processing")
error("Failed to load file")

# In data_processor.py for file-specific logging:
from utils.logger import get_logger

logger = get_logger(base_filename="workpack_001")
logger.info("Processing started")
logger.debug("Detailed processing step...")

# In any module for module-specific logging:
from utils.logger import get_logger

logger = get_logger(module_name="type_coefficient")
logger.info("Loading type coefficients")
logger.warning("Coefficient not found, using default")
"""