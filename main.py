import asyncio
import pandas as pd

from functions.fetching_data import main_fetching_data
from classes.Flag_Detector import FlagDetector
from functions.logger import logger
from functions.Figure_Flag import Figure_Flag
from functions.Reaction_detector import main_reaction_detector
from functions.run_with_retries import run_with_retries

async def main():
    try:
        # Step 1: Fetch Data
        try:
            DataSet, account_info = await run_with_retries(main_fetching_data)
        except RuntimeError as e:
            logger.critical(f"Critical failure in fetching data: {e}")
            # Add emergency measures here, e.g., halting the bot
            return

        print(DataSet)

        # Step 2: Detect Flags
        detector = FlagDetector(DataSet)
        try:
            await run_with_retries(detector.run_detection)
            FLAGS = pd.DataFrame(detector.flags.items(), columns=["Flag Id", "Flag informations"])
            print(FLAGS)
        except RuntimeError as e:
            logger.warning(f"Flag detection failed: {e}")
            FLAGS = pd.DataFrame()  # Ensure FLAGS exists to avoid further errors

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
        # Add high-level emergency handling here

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Critical error in the application lifecycle: {e}")
