import mysql.connector
import asyncio
import pandas as pd
import signal
import sys
import os
import json
from colorama import Fore,Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import The_logger
from functions.run_with_retries import run_with_retries_Function
from classes.timeframe import CTimeFrames
from classes.Metatrader_Module import CMetatrader_Module

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

The_emergency_flag = False
The_emergency_event = asyncio.Event()

async def emergency_listener_Function():
    global The_emergency_flag, config
    emergency_keyword = config["runtime"]["emergency_mode"]["password"]
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if user_input.strip() == emergency_keyword:
            if config["runtime"]["emergency_mode"]["status"]:
                print(Fore.RED + "Emergency trigger activated" + Style.RESET_ALL)
                The_emergency_flag = True
                The_emergency_event.set()
                The_logger.critical("Emergency trigger activated by user input.")
                break
            else:
                print(Fore.YELLOW + "emergency_mode in config is false" + Style.RESET_ALL)

        elif user_input.strip() != emergency_keyword:
            print(Fore.YELLOW + f"Not valid syntax. If you want trigger emergency mode type:{emergency_keyword} and if want to stop code use Ctrl+C" + Style.RESET_ALL)

def emergency_handler_Function(sig, frame):
    The_logger.critical("Process terminated by user.")
    sys.exit(0)

async def main():
    global The_emergency_flag

    while not The_emergency_flag:
        try:
            # Step 1: Updating Data, Flags, and excels of each timeframes
            for The_index, The_timeframe in enumerate(config["trading_configs"]["timeframes"]):
                # Step 1.1: Fetch Data
                try:
                    The_Collected_DataSet = await run_with_retries_Function(CMetatrader_Module.main_fetching_data_Function,The_timeframe)
                except RuntimeError as The_error:
                    The_logger.critical(f"Critical failure in fetching {The_timeframe} data: {The_error}")
                    print(Fore.RED + Style.BRIGHT + f"Critical failure in fetching {The_timeframe} data: {The_error}" +  Style.RESET_ALL)
                    The_emergency_flag = True
                    The_emergency_event.set()
                    The_Collected_DataSet = pd.DataFrame()
                    break

                CTimeFrames[The_index].set_data_Function(The_Collected_DataSet)

                # Step 1.2: Detect Flags
                await run_with_retries_Function(CTimeFrames[The_index].detect_flags_Function)

                # step 1.3: Development
                # await run_with_retries(CTimeFrames[index].development, CMetatrader_Module.mt.account_info())
                
                try:
                    await asyncio.wait_for(The_emergency_event.wait(), timeout=config["runtime"]["time_between_timeframes"])
                except asyncio.TimeoutError:
                    pass
                if The_emergency_flag:
                    break

            #Step 2: update positions
            try:
                await run_with_retries_Function(CMetatrader_Module.Update_Flags_Function)
            except RuntimeError as The_error:
                The_logger.critical(f"Critical failure in updating Positions: {The_error}")
                print(Fore.RED + Style.BRIGHT + f"Critical failure in updating Positions: {The_error}" +  Style.RESET_ALL)

        except Exception as The_error:
            The_logger.critical(f"Unhandled error in main loop: {The_error}")
            The_emergency_flag = True
            The_emergency_event.set()

        # Wait for 5 minutes or until emergency_event is set
        try:
            await asyncio.wait_for(The_emergency_event.wait(), timeout=config["runtime"]["refresh_Data_time"])
        except asyncio.TimeoutError:
            pass

    if The_emergency_flag:
        # Perform emergency actions here
        print(Fore.MAGENTA + "an example of emergency actions is this print" + Style.RESET_ALL)
        The_logger.critical("Performing emergency actions...")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, emergency_handler_Function)
    try:
        The_loop = asyncio.get_event_loop()
        The_loop.create_task(emergency_listener_Function())
        The_loop.run_until_complete(main())
    except Exception as The_error:
        The_logger.critical(f"Critical error in the application lifecycle: {The_error}")