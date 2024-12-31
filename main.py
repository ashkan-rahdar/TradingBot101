import asyncio
import pandas as pd

from functions.fetching_data import main_fetching_data
from classes.Flag_Detector import FlagDetector
from functions.logger import logger
from functions.Figure_Flag import Figure_Flag

async def main():
    try:
        DataSet = await main_fetching_data()
        print(DataSet)
        detector = FlagDetector(DataSet)
        try:
            await detector.run_detection()
            FLAGS = pd.DataFrame(detector.flags.items(),columns= ["Flag Id", "Flag informations"])
            print(FLAGS)
        except Exception as error:
            logger.error(error)

        # try:
        #     Figure_Flag(DataSet, FLAGS)
        # except Exception as error:
        #     logger.error(error)

    except Exception as e:
        print(f"Failed to retrieve data: {e}")

if __name__ == "__main__":
    asyncio.run(main())
