import sys
import os
import pandas as pd
import json
import asyncio
import typing
import bisect
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

from classes.DP_Parameteres import DP_Parameteres_Class
from classes.Flag_Detector import FlagDetector_Class
from classes.Flag import Flag_Class
from functions.logger import print_and_logging_Function
from functions.run_with_retries import run_with_retries_Function
from functions.Reaction_detector import main_reaction_detector
from classes.Database import Database_Class

class Timeframe_Class:
    def __init__(self, The_timeframe: str):
        self.timeframe = The_timeframe
        self.DataSet = pd.DataFrame()
        global config
        self.MySQL_DataBase = Database_Class(The_timeframe)
        self.detector = FlagDetector_Class(The_timeframe, self.MySQL_DataBase)
    
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
            self.dps_to_update = []
            
            valid_DPs = self.MySQL_DataBase._get_tradeable_DPs_Function()
            
            # Pre-calculate these values once
            self.DataSet['time'] = self.DataSet['time'].astype('datetime64[ns]')
            
            tasks = []
            for The_valid_DP, index_of_DP in valid_DPs:
                task = self.Each_DP_validation_Function(The_valid_DP, index_of_DP)
                tasks.append(task)
            
            await asyncio.gather(*tasks)  # Await all tasks
            
            # Batch update the database
            if self.dps_to_update:
                self._batch_update_dp_weights()
                
        except Exception as e:
            print_and_logging_Function("error", f"Error in validating DPs: {e}", "title")
        
    def _batch_update_dp_weights(self):
        """Batch update all DP weights in a single database transaction"""
        try:
            # Prepare the SQL query
            placeholders = ",".join(["%s"] * len(self.dps_to_update))
            values = [(weight, dp_id) for dp_id, weight in self.dps_to_update]
            
            # Execute the update
            self.MySQL_DataBase.cursor.executemany(
                f"UPDATE {self.MySQL_DataBase.important_dps_table_name} SET weight = %s WHERE id = %s", 
                values
            )
            self.MySQL_DataBase.db.commit()
        except Exception as e:
            self.MySQL_DataBase.db.rollback()
            print_and_logging_Function("error", f"Error in batch updating DP weights: {e}", "title")
            
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
                    
            elif aDP.trade_direction == "Bullish":
                # Check if any low price is <= the DP's High price
                if np.any(low_series[index:] <= aDP.High.price):
                    self.dps_to_update.append((The_index_DP, 0))
        
        except Exception as e:
            raise Exception(f"validating the {The_index_DP} DP: {e}")
    
    async def Update_Positions_Function(self):
        valid_DPs = self.MySQL_DataBase._get_tradeable_DPs_Function()
        for The_valid_DP, index_of_DP in valid_DPs:
            print(The_valid_DP)

CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]