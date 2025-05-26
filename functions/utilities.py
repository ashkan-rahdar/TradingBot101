from datetime import datetime, time, timezone
import os
import sys
import time as Time_module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parameters
from classes.Telegrambot import CTelegramBot
from functions.logger import print_and_logging_Function


def is_trading_hours_now():
    now = datetime.now(timezone.utc)  # Timezone-aware UTC time
    weekday = now.weekday()  # Monday = 0, Sunday = 6

    # Define trading window: Monday–Friday, 08:00–21:00 UTC
    allowed_days = range(0, 5)
    start_time = time(5, 0)
    end_time = time(18, 0)
    
    return weekday in allowed_days and start_time <= now.time() <= end_time

def TelegramBot_loop_Funciton():
    while not parameters.shutdown_flag:
        try:
            CTelegramBot.get_updates()
        except Exception as e:
            print_and_logging_Function('error', f'Error in Telegram Bot: {e}')
        Time_module.sleep(10)