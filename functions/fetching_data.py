import MetaTrader5 as mt
import pandas as pd
from datetime import datetime
import json
import sys
import os
from colorama import Fore, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

timeframe_mapping = {
    "M1": mt.TIMEFRAME_M1,
    "M5": mt.TIMEFRAME_M5,
    "M15": mt.TIMEFRAME_M15,
    "M30": mt.TIMEFRAME_M30,
    "H1": mt.TIMEFRAME_H1,
    "H4": mt.TIMEFRAME_H4,
    "D1": mt.TIMEFRAME_D1,
    "W1": mt.TIMEFRAME_W1,
    "MN1": mt.TIMEFRAME_MN1,
}

from functions.logger import logger

async def initialize_mt5():
    if not mt.initialize():
        logger.error("MetaTrader5 initialization failed")
        raise RuntimeError("MetaTrader5 initialization failed")

async def login_mt5() -> mt.AccountInfo:
    global config
    if not mt.login(config["account_info"]["login"], config["account_info"]["password"], config["account_info"]["server"]):
        logger.error("MetaTrader5 login failed")
        raise RuntimeError("MetaTrader5 login failed")
        return None
    else:
        return mt.account_info()

async def fetch_data(timeframe = "M15"):
    global timeframe_mapping
    selected_timeframe = timeframe_mapping.get(timeframe, None)
    try:
        DataSet = pd.DataFrame(mt.copy_rates_from('EURUSD', selected_timeframe, datetime.now(), 10000))
        DataSet['time'] = pd.to_datetime(DataSet["time"], unit='s')
        print(Fore.GREEN + Style.BRIGHT + f"||||||||||||||||||| Data {timeframe} successfully fetched |||||||||||||||||||" + Style.RESET_ALL)
        return DataSet
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise RuntimeError(f"Failed to fetch data: {e}")

async def main_fetching_data(timeframe = 'M15' ):
    try:
        await initialize_mt5()
        account_info = await login_mt5()
        data = await fetch_data(timeframe)
        return data, account_info
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")
        return [], None
    # finally:
    #     mt.shutdown()