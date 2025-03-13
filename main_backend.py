from colorama import Fore,Style
print(Fore.BLUE + Style.BRIGHT + "Welcome To Ashkan's EA..." + Style.RESET_ALL)
import mysql.connector
import asyncio
import pandas as pd
import signal
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import print_and_logging_Function
from functions.run_with_retries import run_with_retries_Function
from classes.timeframe import CTimeFrames
from classes.Metatrader_Module import CMetatrader_Module
import parameters

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

The_emergency_event = asyncio.Event()

async def emergency_listener_Function():
    global config
    emergency_keyword = config["runtime"]["Another_function_syntax"]
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if user_input.strip() == emergency_keyword:
            # if config["runtime"]["Another_function_syntax"]["status"]:
            if True:
                print(Fore.RED + "Emergency trigger activated" + Style.RESET_ALL)
                parameters.The_emergency_flag = True
                The_emergency_event.set()
                print_and_logging_Function("warning", "Emergency trigger activated by user input.", "title")
                break
            else:
                print_and_logging_Function("warning", "emergency_mode in config is false", "title")

        elif user_input.strip() != emergency_keyword:
            print_and_logging_Function("warning", f"Not valid syntax. If you want trigger emergency mode type:{emergency_keyword} and if want to stop code use Ctrl+C", "title")

def emergency_handler_Function(sig, frame):
    print_and_logging_Function("warning", "Process terminated by user.", "title")
    
    print("\n🚨 Emergency Stop Requested! Enter Password to Confirm:")
    user_input = input("Password: ").strip()

    if user_input == config["runtime"]["emergency_mode"]["password"]:
        print("✅ Emergency stop confirmed!")
        The_emergency_flag = True
        sys.exit(1)
    else:
        print("❌ Incorrect password! Ignoring emergency stop.")

    # sys.exit(0)

async def Each_TimeFrame_Function(The_index: int, The_timeframe: str):
    # Step 1: Fetch Data
    if parameters.The_emergency_flag:
        return
    
    try:
        The_Collected_DataSet = await run_with_retries_Function(CMetatrader_Module.main_fetching_data_Function,The_timeframe, CTimeFrames[The_index].DataSet)
    except RuntimeError as The_error:
        print_and_logging_Function("critical", f"Critical failure in fetching {The_timeframe} data: {The_error}", "title")
        parameters.The_emergency_flag = True
        The_emergency_event.set()
        The_Collected_DataSet = pd.DataFrame()
    
    if parameters.The_emergency_flag:
        return
    
    CTimeFrames[The_index].set_data_Function(The_Collected_DataSet)

    # Step 2: Detect Flags
    await run_with_retries_Function(CTimeFrames[The_index].detect_flags_Function)

    # step 3: Validate DPs and Flags
    await run_with_retries_Function(CTimeFrames[The_index].validate_DPs_Function)
    
    # step 4: Development
    # await run_with_retries_Function(CTimeFrames[The_index].development, CMetatrader_Module.mt.account_info())

    try:
        await run_with_retries_Function(CMetatrader_Module.Update_Flags_Function)
    except RuntimeError as The_error:
        print_and_logging_Function("critical", f"Critical failure in updating Positions: {The_error}", "title")

async def main():
    while not parameters.The_emergency_flag:
        try:
            tasks = []
            for The_index, The_timeframe in enumerate(config["trading_configs"]["timeframes"]):
                print_and_logging_Function("info", f"TimeFrame {The_timeframe} :", "description")

                task = asyncio.create_task(Each_TimeFrame_Function(The_index, The_timeframe))
                tasks.append(task)
                if parameters.The_emergency_flag:
                    break
            await asyncio.gather(*tasks)

        except Exception as The_error:
            print_and_logging_Function("critical", f"Unhandled error in main loop: {The_error}", "title")
            parameters.The_emergency_flag = True
            The_emergency_event.set()

    if parameters.The_emergency_flag:
        # Perform emergency actions here
        print_and_logging_Function("critical", "an example of emergency actions is this print", "title")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, emergency_handler_Function)
    signal.signal(signal.SIGTERM, emergency_handler_Function)
    try:
        The_loop = asyncio.get_event_loop()
        The_loop.create_task(emergency_listener_Function())
        The_loop.run_until_complete(main())
    except Exception as The_error:
        print_and_logging_Function("critical", f"Critical error in the application lifecycle: {The_error}", "title")