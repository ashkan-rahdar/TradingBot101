import MetaTrader5
import pandas as pd
from datetime import datetime
import json
import sys
import os
from colorama import Fore, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import logger

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

class Metatrader_Module:
    def __init__(self):
        self.Positions = pd.DataFrame()
        self.mt = MetaTrader5
        self.timeframe_mapping = {
            "M1": self.mt.TIMEFRAME_M1,
            "M5": self.mt.TIMEFRAME_M5,
            "M15": self.mt.TIMEFRAME_M15,
            "M30": self.mt.TIMEFRAME_M30,
            "H1": self.mt.TIMEFRAME_H1,
            "H4": self.mt.TIMEFRAME_H4,
            "D1": self.mt.TIMEFRAME_D1,
            "W1": self.mt.TIMEFRAME_W1,
            "MN1": self.mt.TIMEFRAME_MN1,
        }

    

    async def Update_Flags(self):
        print(Fore.CYAN + Style.BRIGHT + f"you can see mt is transfered successfuly {self.mt}" + Style.RESET_ALL)
    ## for buying price = mt.symbol_info_tick(ticker).ask
    ## for selling price = mt.symbol_info_tick(ticker).bid
    ## order_type= mt.ORDER_TYPE_SELL / BUY

    def Open_position(self, ticker, vol, order_type, price, sl, tp):
        request = {
            "action": self.mt.TRADE_ACTION_DEAL,
            "symbol": ticker,
            "volume": vol,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 101,
            "comment": "My Code opened",
            "type_time": self.mt.ORDER_TIME_GTC,
            "type_filling": self.mt.ORDER_FILLING_FOK
        }
        order = self.mt.order_send(request)
        return order

    #result = Open_position('BTCUSD',0.01, mt.ORDER_TYPE_SELL, mt.symbol_info_tick('BTCUSD').bid, 68000.0, 66000.0)

    #result.retcode


    ## mt.position_get()[0]._asdict('ticket')
    def Close_position(self ,ticker, vol, order_type, price, position):
        request = {
            "action": self.mt.TRADE_ACTION_DEAL,
            "symbol": ticker,
            "volume": vol,
            "type": order_type,
            "position": position,
            "price": price,
            "deviation": 20,
            "magic": 101,
            "comment": "My Code closed",
            "type_time": self.mt.ORDER_TIME_GTC, 
            "type_filling": self.mt.ORDER_FILLING_FOK,
        }
        order = self.mt.order_send(request)
        return order   
    #result = Close_position("BTCUSD", 0.01,mt.ORDER_TYPE_BUY ,mt.symbol_info_tick('BTCUSD').ask ,mt.positions_get()[0]._asdict()['ticket'])
    #print(result)

    async def initialize_mt5(self):
        if not self.mt.initialize():
            logger.error("MetaTrader5 initialization failed")
            print(Fore.RED + Style.BRIGHT + f"MetaTrader5 initialization failed" + Style.RESET_ALL)
            raise RuntimeError("MetaTrader5 initialization failed")

    async def login_mt5(self):
        global config
        if not self.mt.login(config["account_info"]["login"], config["account_info"]["password"], config["account_info"]["server"]):
            logger.error("MetaTrader5 login failed")
            print(Fore.RED + Style.BRIGHT + f"MetaTrader5 login failed" + Style.RESET_ALL)
            raise RuntimeError("MetaTrader5 login failed")
        else:
            # print(Fore.GREEN + Style.BRIGHT + f"logged in as {config['account_info']['login']} in {config['account_info']['server']} server")
            return

    async def fetch_data(self,timeframe = "M15"):
        global timeframe_mapping
        global config
        selected_timeframe = self.timeframe_mapping.get(timeframe, None)
        try:
            symbol_info = self.mt.symbol_info(config["trading_configs"]["asset"])
            if symbol_info is None or not symbol_info.trade_mode:
                print(Fore.CYAN + Style.BRIGHT + "symbol is invalid or market is close now" + Style.RESET_ALL)

            DataSet = pd.DataFrame(self.mt.copy_rates_from_pos(config["trading_configs"]["asset"], 
                                                           selected_timeframe, 
                                                           0, 
                                                           10000))
            DataSet['time'] = pd.to_datetime(DataSet["time"], unit='s')
            print(Fore.GREEN + Style.BRIGHT + f"||||||||||||||||||| Data {timeframe} successfully fetched |||||||||||||||||||" + Style.RESET_ALL)
            return DataSet
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            print(Fore.RED + Style.BRIGHT + f"Failed to fetch data: {e}" + Style.RESET_ALL)
            raise RuntimeError(f"Failed to fetch data: {e}")

    async def main_fetching_data(self ,atimeframe = 'M15' ):
        try:
            await self.initialize_mt5()
            await self.login_mt5()
            print(Fore.BLUE + Style.DIM + f"Fetching {atimeframe} Data..." +  Style.RESET_ALL)
            data = await self.fetch_data(atimeframe)
            print(Fore.BLACK + Style.DIM + f"Fetched {atimeframe} Data: \n{data}" + Style.RESET_ALL)
            return data
        except Exception as e:
            logger.error(f"An error occurred in main_fetching_data: {e}")
            print(Fore.RED + Style.BRIGHT + f"An error occurred in main_fetching_data: {e}" + Style.RESET_ALL)
            return pd.DataFrame
        # finally:
        #     mt.shutdown()

CMetatrader_Module = Metatrader_Module()