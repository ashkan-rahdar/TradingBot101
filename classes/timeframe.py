import sys
import os
import pandas as pd
import json
import asyncio
import typing
import bisect
import numpy as np
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

from classes.DP_Parameteres import DP_Parameteres_Class
from classes.Flag_Detector import FlagDetector_Class
from classes.Metatrader_Module import CMetatrader_Module
from functions.logger import print_and_logging_Function
from functions.run_with_retries import run_with_retries_Function
from functions.Reaction_detector import main_reaction_detector
from classes.Database import Database_Class

class Timeframe_Class:
    def __init__(self, The_timeframe: str):
        self.timeframe = The_timeframe
        self.DataSet = pd.DataFrame()
        global config
        self.CMySQL_DataBase = Database_Class(The_timeframe)
        self.detector = FlagDetector_Class(The_timeframe, self.CMySQL_DataBase)
    
    def set_data_Function(self, aDataSet: pd.DataFrame):
        self.DataSet = aDataSet

    async def detect_flags_Function(self):
        try:
            await run_with_retries_Function(self.detector.run_detection_Function,self.DataSet)
        except RuntimeError as The_error:
            print_and_logging_Function("error", f"{self.timeframe} Flag detection failed: {The_error}", "title")
    
    async def development(self):
        try:
            await run_with_retries_Function(main_reaction_detector, self.DataSet)
        except RuntimeError as e:
            print_and_logging_Function("error", f"Reaction detection failed: {e}", "title")

    async def validate_DPs_Function(self):
        try:
            # Initialize list to store DPs that need to be updated
            self.dps_to_update : list[tuple[int, int]] = []
            self.Tradeable_DPs: list[tuple[DP_Parameteres_Class, int]] = []
            
            valid_DPs = await self.CMySQL_DataBase._get_tradeable_DPs_Function()
            
            # Pre-calculate these values once
            self.DataSet['time'] = self.DataSet['time'].astype('datetime64[ns]')
            
            tasks = []
            for The_valid_DP, index_of_DP in valid_DPs:
                task = self.Each_DP_validation_Function(The_valid_DP, index_of_DP)
                tasks.append(task)
            
            await asyncio.gather(*tasks)  # Await all tasks
            
            # Batch update the database
            if self.dps_to_update:
                try:
                    await self.CMySQL_DataBase._update_dp_weights_Function(self.dps_to_update)
                except Exception as e:
                    raise e
                
        except Exception as e:
            print_and_logging_Function("error", f"Error in validating DPs: {e}", "title")
            
    async def Each_DP_validation_Function(self, aDP: DP_Parameteres_Class, The_index_DP: str):
        try:
            # Pre-calculate these values once outside the loop
            time_series = self.DataSet['time'].to_numpy(dtype='datetime64[ns]')
            high_series = self.DataSet['high'].values
            low_series = self.DataSet['low'].values
            
            if aDP is None or aDP.weight == 0:
                return
            
            index = bisect.bisect_right(time_series, np.datetime64(aDP.first_valid_trade_time))
            
            if index >= len(time_series):
                # raise Exception(f"No Valid Time entered in a {The_index_DP} DP")
                self.Tradeable_DPs.append((aDP, The_index_DP))
                return
            
            # Use NumPy's efficient array operations instead of loops
            if aDP.trade_direction == "Bearish":
                # Check if any high price is >= the DP's Low price
                if np.any(high_series[index:] >= aDP.Low.price):
                    self.dps_to_update.append((The_index_DP, 0))
                else:
                    self.Tradeable_DPs.append((aDP, The_index_DP))
                    
            elif aDP.trade_direction == "Bullish":
                # Check if any low price is <= the DP's High price
                if np.any(low_series[index:] <= aDP.High.price):
                    self.dps_to_update.append((The_index_DP, 0))
                else:
                    self.Tradeable_DPs.append((aDP, The_index_DP))

        except Exception as e:
            raise Exception(f"validating the {The_index_DP} DP: {e}")
    
    async def Update_Positions_Function(self):
        new_opened_positions = 0
        inserting_positions_DB: list[tuple[str, str, float, float, float, datetime.datetime, int, int]] = []

        for aDP, The_index in self.Tradeable_DPs:
            if not The_index in self.CMySQL_DataBase.Traded_DP_Set:
                result = CMetatrader_Module.Open_position_Function(
                    order_type="Buy Limit" if aDP.trade_direction == "Bullish" else "Sell Limit",
                    vol=0.01,
                    price=aDP.High.price if aDP.trade_direction == "Bullish" else aDP.Low.price,
                    sl=aDP.Low.price if aDP.trade_direction == "Bullish" else aDP.High.price,
                    tp=aDP.High.price + 2 * (aDP.High.price - aDP.Low.price) if aDP.trade_direction == "Bullish" else aDP.Low.price - 2 * (aDP.High.price - aDP.Low.price),
                )
                if result.retcode != CMetatrader_Module.mt.TRADE_RETCODE_DONE:
                    print_and_logging_Function("error", f"Error in opening position of DP No.{The_index}. The message \n {result}", "title")
                else:
                    # Get the correct order type from the mapping
                    order_type = CMetatrader_Module.reverse_order_type_mapping.get(result.request.type)

                    inserting_positions_DB.append((
                        The_index,  # traded_dp_id
                        order_type,  # order_type
                        result.request.price,  # price
                        result.request.sl,  # sl
                        result.request.tp,  # tp
                        datetime.datetime.now(),  # Last_modified_time
                        result.request.volume,  # vol
                        result.order  # order_id
                    ))

                    new_opened_positions += 1
                    print_and_logging_Function("info", f"New position opened: DP {The_index}", "description")
        
        try:
            await self.CMySQL_DataBase._insert_positions_batch(inserting_positions_DB)
            if new_opened_positions:
                print_and_logging_Function("info", f"{new_opened_positions} New positions opened and inserted in DB", "title")
        except Exception as e:
            print_and_logging_Function("error", f"Error in inserting position in DB: {e}", "title")

CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]