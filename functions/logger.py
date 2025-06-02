import logging
import os
import sys
import traceback
from logging import FileHandler
import typing
from datetime import datetime
from colorama import Fore, Style
import inspect

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from classes.Telegrambot import CTelegramBot

# Ensure logs directory exists
log_directory = './logs'
os.makedirs(log_directory, exist_ok=True)

# === Custom INFO Handler with 100MB Cap ===
class CappedInfoHandler(FileHandler):
    MAX_SIZE = 100 * 1024 * 1024  # 100 MB

    def emit(self, record):
        try:
            if os.path.exists(self.baseFilename) and os.path.getsize(self.baseFilename) >= self.MAX_SIZE:
                self.close()
                os.remove(self.baseFilename)
                self.stream = self._open()  # Reopen empty file
        except Exception:
            record.msg += f"\n[WARNING] Log rotation failed: {traceback.format_exc()}"
        super().emit(record)

# === Formatter ===
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# === INFO ===
info_handler = CappedInfoHandler(os.path.join(log_directory, "info.log"), mode='a')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(log_formatter)

# === WARNING ===
warning_handler = FileHandler(os.path.join(log_directory, "warning.log"), mode='a')
warning_handler.setLevel(logging.WARNING)
warning_handler.setFormatter(log_formatter)

# === ERROR ===
error_handler = FileHandler(os.path.join(log_directory, "error.log"), mode='a')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_formatter)

# === CRITICAL ===
critical_handler = FileHandler(os.path.join(log_directory, "critical.log"), mode='a')
critical_handler.setLevel(logging.CRITICAL)
critical_handler.setFormatter(log_formatter)

# === LOGGER SETUP ===
The_logger = logging.getLogger("MyLogger")
The_logger.setLevel(logging.DEBUG)
The_logger.handlers.clear()

The_logger.addHandler(info_handler)
The_logger.addHandler(warning_handler)
The_logger.addHandler(error_handler)
The_logger.addHandler(critical_handler)

# === Print & Log Function ===
def print_and_logging_Function(The_type_of_log: typing.Literal["error", "warning", "info", "critical"] = "info", 
                               The_message: str = "", 
                               The_level: typing.Literal["title", "description"] = "title"):

    caller_frame = inspect.stack()[1]
    caller_filename = os.path.basename(caller_frame.filename)
    caller_name = os.path.splitext(caller_filename)[0].replace("_", " ")

    base_message = f"{caller_name}: _______ {The_message} _______"
    if The_level == "description":
        base_message = "         -------> " + base_message

    logger_map = {
        "error": The_logger.error,
        "info": The_logger.info,
        "warning": The_logger.warning,
        "critical": The_logger.critical
    }

    color_map = {
        "error_title": Fore.RED,
        "critical_title": Fore.RED,
        "error_description": Fore.LIGHTRED_EX,
        "critical_description": Fore.LIGHTRED_EX,
        "info_title": Fore.GREEN,
        "info_description": Fore.LIGHTBLACK_EX,
        "warning_title": Fore.YELLOW,
        "warning_description": Fore.LIGHTYELLOW_EX
    }

    style_map = {
        "title": Style.BRIGHT,
        "description": Style.DIM
    }

    logger = logger_map.get(The_type_of_log)
    color = color_map.get(f"{The_type_of_log}_{The_level}")
    style = style_map.get(The_level)

    # === Logging behavior ===
    if The_type_of_log in {"error", "critical"}:
        # Check if we're in an exception context
        exc_info = traceback.format_exc()
        if "NoneType" not in exc_info:
            full_message = f"{base_message}\n[Traceback]\n{exc_info}"
            logger(full_message) # type: ignore
            CTelegramBot.send_message(text= "❌ **Error Detected**: \n\n" + base_message + "❌\n\n Please review the system immediately!")
        else:
            logger(base_message) # type: ignore
    else:
        logger(base_message) # type: ignore

    # === Print to terminal ===
    if The_level == "title":
        timestamp = f"     ({datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')})"
        print(color + style + base_message + Style.RESET_ALL + Fore.LIGHTBLACK_EX + Style.DIM + timestamp + Style.RESET_ALL) # type: ignore
    else:
        print(color + style + base_message + Style.RESET_ALL) # type: ignore

    # Optionally, print traceback to terminal as well
    # if The_type_of_log in {"error", "critical"} and "NoneType" not in exc_info: # type: ignore
    #     print(Fore.LIGHTBLACK_EX + Style.DIM + exc_info + Style.RESET_ALL) # type: ignore

    #     print(color + style + The_message + Style.RESET_ALL) # type: ignore
