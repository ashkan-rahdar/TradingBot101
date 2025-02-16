import mysql.connector
import asyncio
import pandas as pd
import signal
import sys
import os
import json
from colorama import Fore,Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import logger
from functions.run_with_retries import run_with_retries
from classes.timeframe import CTimeFrames
from classes.Metatrader_Module import CMetatrader_Module

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

emergency_flag = False
emergency_event = asyncio.Event()

async def emergency_listener():
    global emergency_flag, config
    emergency_keyword = config["runtime"]["emergency_mode"]["password"]
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if user_input.strip() == emergency_keyword:
            if config["runtime"]["emergency_mode"]["status"]:
                print(Fore.RED + "Emergency trigger activated" + Style.RESET_ALL)
                emergency_flag = True
                emergency_event.set()
                logger.critical("Emergency trigger activated by user input.")
                break
            else:
                print(Fore.YELLOW + "emergency_mode in config is false" + Style.RESET_ALL)

        elif user_input.strip() != emergency_keyword:
            print(Fore.YELLOW + f"Not valid syntax. If you want trigger emergency mode type:{emergency_keyword} and if want to stop code use Ctrl+C" + Style.RESET_ALL)

def emergency_handler(sig, frame):
    logger.critical("Process terminated by user.")
    sys.exit(0)

async def main():
    global emergency_flag

    while not emergency_flag:
        try:
            # Step 1: Updating Data, Flags, and excels of each timeframes
            for index, atimeframe in enumerate(config["trading_configs"]["timeframes"]):
                # Step 1.1: Fetch Data
                try:
                    aDataSet = await run_with_retries(CMetatrader_Module.main_fetching_data,atimeframe)
                except RuntimeError as e:
                    logger.critical(f"Critical failure in fetching {atimeframe} data: {e}")
                    print(Fore.RED + Style.BRIGHT + f"Critical failure in fetching {atimeframe} data: {e}" +  Style.RESET_ALL)
                    emergency_flag = True
                    emergency_event.set()
                    aDataSet = pd.DataFrame()
                    break

                CTimeFrames[index].set_data(aDataSet)

                # Step 1.2: Detect Flags
                await run_with_retries(CTimeFrames[index].detect_flags)

                # step 1.2.1: save to excel
                # await run_with_retries(CTimeFrames[index].save_to_excel)
                # await run_with_retries(CTimeFrames[index].save_to_DB)

                # step 1.3: Development
                # await run_with_retries(CTimeFrames[index].development, CMetatrader_Module.mt.account_info())
                
                try:
                    await asyncio.wait_for(emergency_event.wait(), timeout=config["runtime"]["time_between_timeframes"])
                except asyncio.TimeoutError:
                    pass
                if emergency_flag:
                    break

            #Step 2: update positions
            try:
                await run_with_retries(CMetatrader_Module.Update_Flags)
            except RuntimeError as e:
                logger.critical(f"Critical failure in updating Positions: {e}")
                print(Fore.RED + Style.BRIGHT + f"Critical failure in updating Positions: {e}" +  Style.RESET_ALL)

        except Exception as e:
            logger.critical(f"Unhandled error in main loop: {e}")
            emergency_flag = True
            emergency_event.set()

        # Wait for 5 minutes or until emergency_event is set
        try:
            await asyncio.wait_for(emergency_event.wait(), timeout=config["runtime"]["refresh_Data_time"])
        except asyncio.TimeoutError:
            pass

    if emergency_flag:
        # Perform emergency actions here
        print(Fore.MAGENTA + "an example of emergency actions is this print" + Style.RESET_ALL)
        logger.critical("Performing emergency actions...")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, emergency_handler)
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(emergency_listener())
        loop.run_until_complete(main())
    except Exception as e:
        logger.critical(f"Critical error in the application lifecycle: {e}")