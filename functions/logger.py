import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import traceback
import typing
from colorama import Fore,Style
import inspect
from datetime import datetime

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
The_logger = logging.getLogger("MyLogger")
The_logger.setLevel(logging.DEBUG)

# Add handlers to the logger
The_logger.addHandler(info_handler)
The_logger.addHandler(warning_handler)
The_logger.addHandler(error_handler)
The_logger.addHandler(critical_handler)


def print_and_logging_Function(The_type_of_log: typing.Literal["error", "warning", "info", "critical"] = "info", 
                               The_message: str = "", 
                               The_level: typing.Literal["title", "description"] = "title"):
    
    caller_frame = inspect.stack()[1]
    caller_filename = os.path.basename(caller_frame.filename)
    caller_name = os.path.splitext(caller_filename)[0]  # Remove .py extension
    caller_name = caller_name.replace("_", " ")

    The_message = caller_name + ": _______ " + The_message + " _______"
    if The_level == "description":
        The_message = "         -------> " + The_message

    logger_type_map = {
        "error": The_logger.error,
        "info": The_logger.info,
        "warning": The_logger.warning,
        "critical": The_logger.critical
    }

    printing_color_map = {
        "error_title": Fore.RED,
        "critical_title": Fore.RED,
        "error_description": Fore.LIGHTRED_EX,
        "critical_description": Fore.LIGHTRED_EX,
        "info_title": Fore.GREEN,
        "info_description": Fore.LIGHTBLACK_EX,
        "warning_title": Fore.YELLOW,
        "warning_description": Fore.LIGHTYELLOW_EX
    }

    printing_style_map = {
        "title" : Style.BRIGHT,
        "description": Style.DIM
    }

    logger_type = logger_type_map.get(The_type_of_log, None)
    printing_color = printing_color_map.get(The_type_of_log+"_"+The_level, None)
    printing_style = printing_style_map.get(The_level, None)

    logger_type(The_message)

    if The_level == "title":
        The_printing_time = f"     ({datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')})"
        print(printing_color + printing_style + The_message + Style.RESET_ALL + Fore.LIGHTBLACK_EX + Style.DIM + The_printing_time + Style.RESET_ALL)
    else:
        print(printing_color + printing_style + The_message + Style.RESET_ALL)