import MetaTrader5 as mt
import pandas as pd
from datetime import datetime
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

from functions.logger import logger

async def initialize_mt5():
    if not mt.initialize():
        logger.error("MetaTrader5 initialization failed")
        raise RuntimeError("MetaTrader5 initialization failed")

async def login_mt5(config):
    if not mt.login(config["account_info"]["login"], config["account_info"]["password"], config["account_info"]["server"]):
        logger.error("MetaTrader5 login failed")
        raise RuntimeError("MetaTrader5 login failed")

async def fetch_data():
    try:
        DataSet = pd.DataFrame(mt.copy_rates_from('EURUSD', mt.TIMEFRAME_M5, datetime.now(), 10000))
        DataSet['time'] = pd.to_datetime(DataSet["time"], unit='s')
        return DataSet
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise RuntimeError(f"Failed to fetch data: {e}")

async def main_fetching_data():
    try:
        await initialize_mt5()
        global config
        await login_mt5(config)
        data = await fetch_data()
        return data
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")
        return []
    # finally:
    #     mt.shutdown()