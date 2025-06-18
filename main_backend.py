from colorama import Fore,Style
print(Fore.BLUE + Style.BRIGHT + "Welcome To Ashkan's EA..." + Style.RESET_ALL)
import mysql.connector  # noqa: E402, F401
import asyncio  # noqa: E402
import pandas as pd  # noqa: E402
import signal  # noqa: E402
import sys  # noqa: E402
import os  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
import cProfile  # noqa: E402
import threading  # noqa: E402
# import subprocess  # noqa: E402

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import print_and_logging_Function  # noqa: E402
from functions.run_with_retries import run_with_retries_Function  # noqa: E402
from classes.timeframe import CTimeFrames  # noqa: E402
from classes.Metatrader_Module import CMetatrader_Module  # noqa: E402
from functions.utilities import is_trading_hours_now, TelegramBot_loop_Funciton  # noqa: E402
import parameters  # noqa: E402

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

async def shutdown_Function():
    """
    Asynchronous function that listens for user input to trigger an emergency mode.
    This function continuously monitors user input from the standard input (stdin) 
    and checks if it matches a predefined emergency keyword. If the keyword is 
    detected, it activates an emergency flag, sets an emergency event, and logs 
    the activation. If the input does not match the keyword, it logs a warning 
    message instructing the user on how to trigger the emergency mode or stop the 
    program.
    Inputs:
    - None: The function does not take any direct arguments. It relies on the 
        global `config` dictionary for configuration and the `parameters` and 
        `The_emergency_event` objects for managing the emergency state.
    Outputs:
    - None: The function does not return any value. It performs actions such as 
        setting flags, triggering events, and logging messages as side effects.
    Key Components:
    - `config["runtime"]["Another_function_syntax"]`: The emergency keyword 
        defined in the runtime configuration.
    - `user_input`: Captures user input from the standard input asynchronously.
    - `parameters.The_emergency_flag`: A global flag that is set to `True` when 
        the emergency mode is activated.
    - `The_emergency_event.set()`: Signals that the emergency event has been 
        triggered.
    - `print_and_logging_Function`: Logs messages to the console and/or a log 
        file, depending on the severity and context of the message.
    Behavior:
    - If the user input matches the emergency keyword, the function activates 
        the emergency mode, logs a warning message, and exits the loop.
    - If the user input does not match the emergency keyword, it logs a warning 
        message instructing the user on the correct syntax or how to stop the 
        program.
    """
    def handle_shutdown():
        print_and_logging_Function("info", "Shutting down gracefully...")
        parameters.shutdown_flag = True
        
    def handle_restart():
        print_and_logging_Function("info", "Restarting bot gracefully...")
        # parameters.restart_flag = True
        # parameters.shutdown_flag = True
        
    def handle_change_seed():
        print("Changing ML seed...")
        # Randomize or ask for new seed input

    def handle_close_positions():
        print("Closing all positions...")
        # Call your broker API to close all open trades
        
    COMMANDS = {
        "restart": handle_restart,
        "shutdown": handle_shutdown,
        "change the ML seed": handle_change_seed,
        "close all positions": handle_close_positions
    }
    
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        user_input = user_input.lower().strip()

        command_fn = COMMANDS.get(user_input)
        if command_fn:
            command_fn()

            # if parameters.restart_flag:
            #     print("Relaunching bot...")
            #     subprocess.Popen([sys.executable] + sys.argv)  # Starts a new instance
            #     print("Shutting down current instance...")
            #     sys.exit(1) 
            break  # Exit the current bot instance
        else:
            print_and_logging_Function("warning", f"Not valid syntax. Your Input: {user_input}. \n Valid Inputs: {list(COMMANDS.keys())}", "title")

def emergency_handler_Function(sig, frame):
    try:
        print_and_logging_Function("warning", "Process terminated by user.", "title")

        print("\n🚨 Emergency Stop Requested! Enter Password to Confirm:")
        user_input = input("Password: ").strip()

        if user_input == config["runtime"]["emergency_mode"]["password"]:
            print("✅ Emergency stop confirmed!")
            sys.exit(1)
        else:
            print("❌ Incorrect password! Ignoring emergency stop.")
    except Exception as e:
        print_and_logging_Function("error",f"Error in shutting down bot emergency: {e}", "title")
        
async def Each_TimeFrame_Function(The_index: int, The_timeframe: str):
    """
    Asynchronous function `Each_TimeFrame_Function` processes data for a specific timeframe in a trading bot system.
    This function performs the following steps:
    1. **Fetch Data**: Retrieves data for the specified timeframe using a retry mechanism. If an error occurs during data fetching, it logs the error, sets an emergency flag, and halts further processing.
    2. **Set Data**: Updates the corresponding timeframe object with the fetched dataset.
    3. **Detect Flags**: Identifies specific conditions or flags in the data for the given timeframe.
    4. **Validate DPs and Flags**: Validates detected flags and decision points (DPs) to ensure they meet the required criteria.
    5. **Update Positions**: Updates trading positions based on the processed data. If an error occurs during this step, it logs the error as critical.
    ### Parameters:
    - `The_index` (int): The index of the timeframe being processed. This is used to access the corresponding timeframe object from a predefined list.
    - `The_timeframe` (str): The string representation of the timeframe being processed (e.g., "1H", "4H", "1D").
    ### Returns:
    - None: This function does not return any value. It performs operations on global or shared objects and logs the results.
    ### Additional Notes:
    - The function uses a retry mechanism (`run_with_retries_Function`) to handle transient errors during asynchronous operations.
    - If an emergency flag (`parameters.The_emergency_flag`) is set, the function halts further processing to prevent cascading failures.
    - Execution time for each loop is logged for performance monitoring.
    - The function is wrapped in a try-except block to handle unexpected errors gracefully and log them appropriately.
    """
    
    try:
        start_time = time.time()
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Step 1: Fetch Data
        if parameters.shutdown_flag:
            return
        
        try:
            The_Collected_DataSet = await run_with_retries_Function(CMetatrader_Module.main_fetching_data_Function,The_timeframe, CTimeFrames[The_index].DataSet)
        except RuntimeError as The_error:
            print_and_logging_Function("critical", f"Critical failure in fetching {The_timeframe} data: {The_error}", "title")
            parameters.shutdown_flag = True
            The_Collected_DataSet = pd.DataFrame()
        
        if parameters.shutdown_flag:
            return
        
        CTimeFrames[The_index].set_data_Function(The_Collected_DataSet)

        # Step 2: Detect Flags
        try:
            await run_with_retries_Function(CTimeFrames[The_index].detect_flags_Function)
        except RuntimeError as The_error:
            print_and_logging_Function("critical", f"Critical failure in flag detection {The_timeframe}: {The_error}", "title")
            
        if parameters.shutdown_flag:
            return

        # step 3: Validate DPs and Flags
        try:
            await run_with_retries_Function(CTimeFrames[The_index].validate_DPs_Function)
        except RuntimeError as The_error:
            print_and_logging_Function("critical", f"Critical failure in validating DPs {The_timeframe}: {The_error}", "title")
        
        if parameters.shutdown_flag:
            return
        # step 4: Train ML
        try:
            await run_with_retries_Function(CTimeFrames[The_index].ML_Main_Function)
        except RuntimeError as The_error:
            print_and_logging_Function("critical", f"Critical failure in ML {The_timeframe}: {The_error}", "title")
        
        if parameters.shutdown_flag:
            return    
        
        # step 5: Update and open Positions
        try:
            await run_with_retries_Function(CTimeFrames[The_index].Update_Positions_Function)
        except RuntimeError as The_error:
            print_and_logging_Function("critical", f"Critical failure in updating Positions {The_timeframe}: {The_error}", "title")

        profiler.disable()
        elapsed = time.time() - start_time
        if config['runtime']['develop_mode'] :
            print_and_logging_Function("info",f"For Each loop of Each timeframe: {elapsed:.2f} seconds", "title")
            # profiler.print_stats(sort='cumtime')
        
        # preventing spam requests
        await asyncio.sleep(60)
    except Exception as e:
        print_and_logging_Function("error", f"Error in validating DPs: {e}", "title")

async def main():   
    while not parameters.shutdown_flag:
        try:
            if not (is_trading_hours_now() or config['runtime']['develop_mode']):
                print_and_logging_Function("info", "Outside trading hours. Closing positions and sleeping until next Valid Time...", "title")
                
                for The_index, The_timeframe in enumerate(config["trading_configs"]["timeframes"]):
                    print_and_logging_Function("info", f"Closing Postions of {The_timeframe}", "description")
                    await CTimeFrames[The_index].Closing_positions_Function()

                try:
                    for The_index, The_timeframe in enumerate(config["trading_configs"]["timeframes"]):
                        print_and_logging_Function("info", f"Calculating the Result of {The_timeframe}", "description")
                        await CTimeFrames[The_index].Result_Reporter_Function()
                except Exception as e:
                    print_and_logging_Function("error",f"Error in Reporting the Result of timeframes: {e}")
                    
                while not is_trading_hours_now():
                    await asyncio.sleep(60)
                    if parameters.shutdown_flag:
                        break
                
                print_and_logging_Function("info", "Inside trading hours. Starting Bot again...", "title")
                continue
            
            if parameters.shutdown_flag:
                break
            
            tasks = []
            for The_index, The_timeframe in enumerate(config["trading_configs"]["timeframes"]):
                print_and_logging_Function("info", f"TimeFrame {The_timeframe} :", "description")
                task = asyncio.create_task(Each_TimeFrame_Function(The_index, The_timeframe))
                tasks.append(task)

                if parameters.shutdown_flag:
                    break

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as The_error:
            print_and_logging_Function("critical", f"Unhandled error in main loop: {The_error}", "title")
            parameters.shutdown_flag = True

    if parameters.shutdown_flag:
        print_and_logging_Function("info", "Shutting down! Canceling all open positions and cleaning DB. Please wait...", "title")

        for The_index, The_timeframe in enumerate(config["trading_configs"]["timeframes"]):
            print_and_logging_Function("info", f"Closing Postions of {The_timeframe}", "description")
            await CTimeFrames[The_index].Closing_positions_Function()
        sys.exit(1)

if __name__ == "__main__":
    parameters.shutdown_flag = False
    signal.signal(signal.SIGINT, emergency_handler_Function)
    signal.signal(signal.SIGTERM, emergency_handler_Function)

    # Start Telegram bot in background thread
    telegram_thread = threading.Thread(target=TelegramBot_loop_Funciton, daemon=True)
    telegram_thread.start()

    try:
        The_loop = asyncio.get_event_loop()
        The_loop.create_task(shutdown_Function())
        The_loop.run_until_complete(main())
    except Exception as The_error:
        print_and_logging_Function("critical", f"Critical error in the application lifecycle: {The_error}", "title")