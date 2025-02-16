import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure that the 'logs' directory exists
log_directory = './logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Custom filter for separating log levels
class LogLevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno == self.level

# Custom error handler to log full traceback
class FullTracebackHandler(RotatingFileHandler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:  # Only for ERROR and CRITICAL logs
            record.msg += f"\n{traceback.format_exc()}"  # Append traceback
        super().emit(record)

# Set up a formatter
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Create handlers for each log level
info_handler = RotatingFileHandler("logs/info.log", maxBytes=5 * 1024 * 1024, backupCount=3)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(log_formatter)
info_handler.addFilter(LogLevelFilter(logging.INFO))

warning_handler = RotatingFileHandler("logs/warning.log", maxBytes=5 * 1024 * 1024, backupCount=3)
warning_handler.setLevel(logging.WARNING)
warning_handler.setFormatter(log_formatter)
warning_handler.addFilter(LogLevelFilter(logging.WARNING))

# Use FullTracebackHandler for error and critical logs
error_handler = FullTracebackHandler("logs/error.log", maxBytes=5 * 1024 * 1024, backupCount=3)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_formatter)
error_handler.addFilter(LogLevelFilter(logging.ERROR))

critical_handler = FullTracebackHandler("logs/critical.log", maxBytes=5 * 1024 * 1024, backupCount=3)
critical_handler.setLevel(logging.CRITICAL)
critical_handler.setFormatter(log_formatter)
critical_handler.addFilter(LogLevelFilter(logging.CRITICAL))

# Create the main logger
logger = logging.getLogger("MyLogger")
logger.setLevel(logging.DEBUG)

# Add handlers to the logger
logger.addHandler(info_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)
logger.addHandler(critical_handler)