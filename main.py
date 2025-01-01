import asyncio
import pandas as pd
import signal
import sys
import json
from colorama import Fore,Style

from functions.fetching_data import main_fetching_data
from classes.Flag_Detector import FlagDetector
from functions.logger import logger
from functions.Figure_Flag import Figure_Flag
from functions.Reaction_detector import main_reaction_detector
from functions.run_with_retries import run_with_retries

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

        elif user_input.strip() != "ashkan":
            print(Fore.YELLOW + f"Not valid syntax. If you want trigger emergency mode type:{emergency_keyword} and if want to stop code use Ctrl+C" + Style.RESET_ALL)

def emergency_handler(sig, frame):
    logger.critical("Process terminated by user.")
    sys.exit(0)

async def main():
    global emergency_flag
    detector = FlagDetector()

    while not emergency_flag:
        try:
            # Step 1: Fetch Data
            try:
                print(Fore.BLUE + Style.DIM + "Fetching Data..." +  Style.RESET_ALL)
                DataSet, account_info = await run_with_retries(main_fetching_data)
            except RuntimeError as e:
                logger.critical(f"Critical failure in fetching data: {e}")
                emergency_flag = True
                emergency_event.set()
                break

            print(Fore.BLACK + Style.DIM + f"Data: \n{DataSet}" + Style.RESET_ALL)

            # Step 2: Detect Flags
            try:
                await run_with_retries(detector.run_detection,DataSet)
                FLAGS = pd.DataFrame(detector.flags.items(), columns=["Flag Id", "Flag informations"])
                print(Fore.BLACK + Style.DIM + f"Flags: \n {FLAGS}" + Style.RESET_ALL)
            except RuntimeError as e:
                logger.warning(f"Flag detection failed: {e}")
                FLAGS = pd.DataFrame()

            # Step 3: Visualize Flags
            try:
                Figure_Flag(DataSet, FLAGS)
            except Exception as e:
                logger.error(f"Visualization failed: {e}")

            # Step 4: React to Flags
            try:
                await run_with_retries(main_reaction_detector, FLAGS, DataSet, account_info.balance)
            except RuntimeError as e:
                logger.warning(f"Reaction detection failed: {e}")
                # Emergency fallback action, e.g., reset trades

        except Exception as e:
            logger.critical(f"Unhandled error in main loop: {e}")
            emergency_flag = True
            emergency_event.set()

        # Wait for 5 minutes or until emergency_event is set
        try:
            await asyncio.wait_for(emergency_event.wait(), timeout=config["runtime"]["refresh_time"])
        except asyncio.TimeoutError:
            pass

    if emergency_flag:
        # Perform emergency actions here
        print("an example of emergency actions is this print")
        logger.critical("Performing emergency actions...")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, emergency_handler)
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(emergency_listener())
        loop.run_until_complete(main())
    except Exception as e:
        logger.critical(f"Critical error in the application lifecycle: {e}")