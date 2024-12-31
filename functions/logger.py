import logging
from logging.handlers import RotatingFileHandler
import os
import sys

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

error_handler = RotatingFileHandler("logs/error.log", maxBytes=5 * 1024 * 1024, backupCount=3)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_formatter)
error_handler.addFilter(LogLevelFilter(logging.ERROR))

# Create the main logger
logger = logging.getLogger("MyLogger")
logger.setLevel(logging.DEBUG)

# Add handlers to the logger
logger.addHandler(info_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)