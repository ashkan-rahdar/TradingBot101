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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import print_and_logging_Function  # noqa: E402
from functions.run_with_retries import run_with_retries_Function  # noqa: E402
from classes.timeframe import CTimeFrames  # noqa: E402
from classes.Metatrader_Module import CMetatrader_Module  # noqa: E402
import parameters  # noqa: E402

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

The_emergency_event = asyncio.Event()

async def emergency_listener_Function():
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
    """
    Handles emergency stop requests by prompting the user for a password to confirm the action.
    This function is triggered by a signal (e.g., SIGINT) and allows the user to terminate the process 
    gracefully by entering a predefined password. If the password matches the expected value, the 
    process exits with a status code of 1. Otherwise, the emergency stop request is ignored.
    Args:
        sig (int): The signal number that triggered the handler.
        frame (FrameType): The current stack frame when the signal was received.
    Behavior:
        - Logs a warning message indicating that the process was terminated by the user.
        - Prompts the user to enter a password for confirming the emergency stop.
        - Compares the entered password with the expected password from the configuration.
        - If the password matches, sets an emergency flag and exits the process with a status code of 1.
        - If the password does not match, logs a message and ignores the emergency stop request.
    Returns:
        None
    """
    
    print_and_logging_Function("warning", "Process terminated by user.", "title")
    
    print("\n🚨 Emergency Stop Requested! Enter Password to Confirm:")
    user_input = input("Password: ").strip()

    if user_input == config["runtime"]["emergency_mode"]["password"]:
        print("✅ Emergency stop confirmed!")
        The_emergency_flag = True  # noqa: F841
        sys.exit(1)
    else:
        print("❌ Incorrect password! Ignoring emergency stop.")

    # sys.exit(0)

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
            await run_with_retries_Function(CTimeFrames[The_index].Update_Positions_Function)
        except RuntimeError as The_error:
            print_and_logging_Function("critical", f"Critical failure in updating Positions: {The_error}", "title")


        profiler.disable()
        elapsed = time.time() - start_time
        print_and_logging_Function("info",f"For Each loop of Each timeframe: {elapsed:.2f} seconds", "title")
        # profiler.print_stats(sort='cumtime')
    except Exception as e:
        print_and_logging_Function("error", f"Error in validating DPs: {e}", "title")

async def main():
    """
    The `main` function serves as the primary asynchronous entry point for the trading bot's backend logic. 
    It continuously executes tasks for each configured trading timeframe until an emergency flag is triggered.
    Functionality:
    - Iterates over a list of trading timeframes defined in the configuration.
    - For each timeframe, it creates and schedules an asynchronous task to process trading logic using `Each_TimeFrame_Function`.
    - Handles exceptions that may occur during the execution of the main loop, logging critical errors and triggering emergency actions if necessary.
    - If the emergency flag (`parameters.The_emergency_flag`) is set, it performs predefined emergency actions.
    Inputs:
    - This function does not take any direct arguments. Instead, it relies on global variables and configurations:
        - `parameters.The_emergency_flag`: A boolean flag indicating whether an emergency has occurred.
        - `config["trading_configs"]["timeframes"]`: A list of timeframes for which trading tasks are executed.
        - `Each_TimeFrame_Function`: An asynchronous function that processes trading logic for a specific timeframe.
        - `print_and_logging_Function`: A utility function for logging messages with different severity levels.
        - `The_emergency_event`: An event object used to signal emergency conditions.
    Outputs:
    - The function does not return any value. It performs its operations asynchronously and relies on side effects such as:
        - Logging messages to indicate progress or errors.
        - Scheduling and executing trading tasks for each timeframe.
        - Triggering emergency actions when necessary.
    """
    
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