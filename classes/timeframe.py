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
            
    async def Each_DP_validation_Function(self, aDP: DP_Parameteres_Class, The_index_DP: int):
        try:
            # Pre-calculate these values once outside the loop
            time_series = self.DataSet['time'].to_numpy(dtype='datetime64[ns]')
            high_series = self.DataSet['high'].values
            low_series = self.DataSet['low'].values
            
            if aDP is None or aDP.weight == 0:
                return
            
            index = bisect.bisect_right(time_series, np.datetime64(aDP.first_valid_trade_time))
            
            if index >= len(time_series):
                raise Exception(f"No Valid Time entered in a {The_index_DP} DP")
            
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
        for aDP, The_index in self.Tradeable_DPs:
            if not The_index in self.CMySQL_DataBase.Traded_DP_Set:
                result = CMetatrader_Module.Open_position_Function(order_type= "Buy Limit" if aDP.trade_direction == "Bullish" else "Sell Limit",
                                                        vol= 0.01,
                                                        price= aDP.High.price if aDP.trade_direction == "Bullish" else aDP.Low.price,
                                                        sl= aDP.Low.price if aDP.trade_direction == "Bullish" else aDP.High.price,
                                                        tp= aDP.High.price + 2*(aDP.High.price-aDP.Low.price) if aDP.trade_direction == "Bullish" else aDP.Low.price - 2*(aDP.High.price - aDP.Low.price),
                                                        )
                if result.retcode != CMetatrader_Module.mt.TRADE_RETCODE_DONE:
                    print_and_logging_Function("error", f"Error in opening position of DP No.{The_index}. The message \n {result}", "title")
                else:
                    try:    
                        Position_row_id = await self.CMySQL_DataBase._insert_position(traded_dp_id=The_index, 
                                                            mt_order_type=result.request.type,
                                                            price= result.request.price, 
                                                            sl= result.request.sl,
                                                            tp= result.request.tp,
                                                            Last_modified_time= datetime.datetime.now(),
                                                            vol= result.request.volume,
                                                            order_id= result.order, 
                                                            order_type_mapping= CMetatrader_Module.reverse_order_type_mapping)
                        # CMetatrader_Module.cancel_order(order_number= result.order)

                        print_and_logging_Function("info", f"New position submitted which saved in {Position_row_id} row of DB", "title")
                    except Exception as e:
                        print_and_logging_Function("error", f"Error in inserting position in DB: {e}", "title")

CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]