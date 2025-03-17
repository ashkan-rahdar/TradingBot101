import MetaTrader5
import pandas as pd
from datetime import datetime
import json
import sys
import os
import asyncio
from colorama import Fore, Style
import typing

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import print_and_logging_Function
import parameters
from classes.Database import Database_Class

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

class Metatrader_Module_Class:
    def __init__(self):
        global config
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
        self.order_type_mapping = {
            "Buy": self.mt.ORDER_TYPE_SELL,
            "Sell": self.mt.ORDER_TYPE_SELL,
            "Buy Limit": self.mt.ORDER_TYPE_BUY_LIMIT,
            "Sell Limit": self.mt.ORDER_TYPE_SELL_LIMIT
        }
        # self.reverse_order_type_mapping = {
        #     self.mt.ORDER_TYPE_SELL: "Buy",
        #     self.mt.ORDER_TYPE_SELL: "Sell",
        #     self.mt.ORDER_TYPE_BUY_LIMIT: "Buy Limit",
        #     self.mt.ORDER_TYPE_SELL_LIMIT: "Sell Limit"
        # }
        self.reverse_order_type_mapping = {value: key for key, value in self.order_type_mapping.items()}

    def Open_position_Function(self, 
                            order_type: typing.Literal["Buy", "Sell", "Buy Limit", "Sell Limit"], 
                            vol: float, 
                            price: float, 
                            sl: float, 
                            tp: float, 
                            ticker: str = config["trading_configs"]["asset"]):
        
        order_type = self.order_type_mapping.get(order_type, None)
        
        # Get number of decimal places for the asset dynamically
        symbol_info = self.mt.symbol_info(ticker)
        if symbol_info is None:
            print(f"Error: Could not retrieve symbol info for {ticker}")
            return None, None
        
        digits = symbol_info.digits  # Number of decimal places for the symbol

        request = {
            "action": self.mt.TRADE_ACTION_DEAL if order_type < 2 else self.mt.TRADE_ACTION_PENDING,
            "symbol": ticker,
            "volume": vol,
            "type": order_type,
            "price": round(price, digits),  # Dynamically rounding based on symbol
            "sl": round(sl, digits),
            "tp": round(tp, digits),
            "deviation": 20,
            "magic": 101,
            "comment": "My Code opened",
            "type_time": self.mt.ORDER_TIME_GTC,
            "type_filling": self.mt.ORDER_FILLING_FOK
        }
        return self.mt.order_send(request)

    def partial_close(self, ticket: int, ratio: float  = 1):
        """
        Partially closes a position based on the given ticket and ratio.
        
        :param ticket: The position ticket (order ID).
        :param ratio: The fraction of the position to close (0 to 1).
        """
        # Ensure ratio is within valid range
        if not (0 < ratio <= 1):
            print("Invalid ratio. It must be between 0 and 1.")
            return False

        # Get open positions
        positions = self.mt.positions_get()

        if positions is None:
            print("No open positions")
            return False

        # Find the position with the given ticket
        position = next((p for p in positions if p.ticket == ticket), None)
        
        if position is None:
            print(f"No position found with ticket {ticket}")
            return False

        # Calculate volume to close
        volume_to_close = position.volume * ratio

        # Ensure the volume to close is valid (mt might have minimum volume limits)
        if volume_to_close < self.mt.symbol_info(position.symbol).volume_min:
            print(f"Volume to close ({volume_to_close}) is less than the minimum allowed.")
            return False

        # Create a close request
        close_request = {
            "action": self.mt.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": volume_to_close,
            "price": position.price_current,
            "type": self.mt.ORDER_TYPE_SELL if position.type == self.mt.POSITION_TYPE_BUY else self.mt.ORDER_TYPE_BUY,
            "position": ticket,
            "magic": 123456,
            "comment": "Partial close",
        }

        # Send the close order
        result = self.mt.order_send(close_request)

        if result and result.retcode == self.mt.TRADE_RETCODE_DONE:
            print(f"Successfully closed {ratio*100:.1f}% of position {ticket}. Remaining volume: {position.volume - volume_to_close:.2f}")
            return True
        else:
            print(f"Failed to partially close position {ticket}. Error code: {result.retcode}")
            return False

    def cancel_order(self, order_number):
        # Create the request
        request = {
            "action": self.mt.TRADE_ACTION_REMOVE,
            "order": order_number,
            "comment": "Order Removed"
        }
        # Send order to mt
        order_result = self.mt.order_send(request)
        return order_result
    
    async def initialize_mt5_Function(self):
        if not self.mt.initialize():
            print_and_logging_Function("error", "MetaTrader5 initialization failed", "title")
            raise RuntimeError("MetaTrader5 initialization failed")

    async def login_mt5_Function(self):
        global config
        if not self.mt.login(config["account_info"]["login"], config["account_info"]["password"], config["account_info"]["server"]):
            print_and_logging_Function("error", "MetaTrader5 login failed", "title")
            raise RuntimeError("MetaTrader5 login failed")

    async def fetch_data_Function(self, The_timeframe = "M15", The_Dataset: pd.DataFrame = pd.DataFrame()):
        selected_timeframe = self.timeframe_mapping.get(The_timeframe, None)
        try:
            symbol_info = self.mt.symbol_info(config["trading_configs"]["asset"])
            if symbol_info is None or not symbol_info.trade_mode:
                print_and_logging_Function("error", "symbol is invalid or market is close now", "description")

            if len(The_Dataset) != 0:
                    print_and_logging_Function("info", f"Waiting for new {The_timeframe} candles...", "description")

            while not parameters.The_emergency_flag:
                DataSet = pd.DataFrame(self.mt.copy_rates_from_pos(config["trading_configs"]["asset"], 
                                                            selected_timeframe, 
                                                            0, 
                                                            10000))
                DataSet['time'] = pd.to_datetime(DataSet["time"], unit='s')
                
                if len(The_Dataset) == 0 or The_Dataset['time'].iloc[-1] != DataSet['time'].iloc[-1]:
                    print_and_logging_Function("info", f"Data {The_timeframe} successfully fetched", "title")
                    return DataSet
                
                await asyncio.sleep(30)
            return pd.DataFrame()
        
        except Exception as e:
            print_and_logging_Function("error", f"Failed to fetch data: {e}", "title")
            raise RuntimeError(f"Failed to fetch data: {e}")

    async def main_fetching_data_Function(self, atimeframe = 'M15', aDataset: pd.DataFrame = pd.DataFrame()) -> pd.DataFrame:
        try:
            await self.initialize_mt5_Function()
            await self.login_mt5_Function()
            print_and_logging_Function("info",  f"Fetching {atimeframe} Data...", "description")
            The_data = await self.fetch_data_Function(atimeframe, aDataset)
            if len(The_data) > 0:
                print_and_logging_Function("info", f"10000 candles in {atimeframe} fetched from {The_data['time'][0]} to {The_data['time'][len(The_data['time']) - 1]}", "description")
            return The_data
        except Exception as The_error:
            print_and_logging_Function("error", f"An error occurred in main_fetching_data: {The_error}", "title")
            return pd.DataFrame()
        # finally:
        #     mt.shutdown()

CMetatrader_Module = Metatrader_Module_Class()