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
            # Get the total number of rows in the table
            self.MySQL_DataBase.cursor.execute(f"SELECT COUNT(*) FROM {self.MySQL_DataBase.flags_table_name}")
            row_count = self.MySQL_DataBase.cursor.fetchone()[0]  # Fetch the count value

        except Exception as e:
            print_and_logging_Function("error", f"Error retrieving row count: {e}", "title")
            return

        tasks = []
        # Iterate through all rows from 1 to row_count
        for flag_id in range(1, row_count + 1):
            task = self.Each_Flag_fetch_data_Function(flag_id)  # No need to use create_task()
            tasks.append(task)

        await asyncio.gather(*tasks)  # Await all tasks

    async def Each_Flag_fetch_data_Function(self, flag_id):

        def Is_DP_used_Function(The_DP: DP_Parameteres_Class, 
                                End_of_flag: pd.Timestamp, 
                                type_of_flag: typing.Literal['Bearish','Bullish'], 
                                DP_id : int) -> bool:
            if The_DP is None:
                return False
            
            time_series = self.DataSet['time'].to_numpy(dtype='datetime64[ns]')
            index = bisect.bisect_right(time_series, np.datetime64(End_of_flag)) # Binary search for the first index where time > End_of_flag
            
            if index < len(time_series):
                First_seaching_index = index
            else:
                raise Exception(f"No Valid Time entered in a {DP_id} DP")
            
            if type_of_flag == "Bearish":
                high_series = self.DataSet['high'].values  # Convert to NumPy array for fast lookup
                for i in range(First_seaching_index, len(high_series)):  # Scan from found index onward
                    if high_series[i] >= The_DP.Low.price:
                        return True

                return False
                        
            elif type_of_flag == "Bullish":
                low_series = self.DataSet['low'].values  # Convert to NumPy array for fast lookup
                for i in range(First_seaching_index, len(low_series)):  # Scan from found index onward
                    if low_series[i] <= The_DP.High.price:
                        return True

                return False
            
            else:
                return True

        try:
            # ✅ Create a NEW cursor for this async function
            db_cursor = self.MySQL_DataBase.db.cursor()

            # Fetch the values of "type", "FTC", "EL", and "MPL" for the current row
            db_cursor.execute(
                f"SELECT type, Ending_time, FTC, EL, MPL FROM {self.MySQL_DataBase.flags_table_name} WHERE id = %s",
                (flag_id,)
            )
            result = db_cursor.fetchone()  # Fetch one row

            if result:
                type_of_flag, End_time_of_flag, FTC_id_of_flag, EL_id_of_flag, MPL_id_of_flag = result  # Unpack values

                FTC_of_flag = self.MySQL_DataBase._get_important_dp_Function(FTC_id_of_flag)
                EL_of_flag = self.MySQL_DataBase._get_important_dp_Function(EL_id_of_flag)
                MPL_of_flag = self.MySQL_DataBase._get_important_dp_Function(MPL_id_of_flag)

                if Is_DP_used_Function(FTC_of_flag, End_time_of_flag, type_of_flag, FTC_id_of_flag):
                    self.MySQL_DataBase.set_important_dp_weight_Function(FTC_id_of_flag, 0)
                if Is_DP_used_Function(EL_of_flag, End_time_of_flag, type_of_flag, EL_id_of_flag):
                    self.MySQL_DataBase.set_important_dp_weight_Function(EL_id_of_flag, 0)
                if Is_DP_used_Function(MPL_of_flag, End_time_of_flag, type_of_flag, MPL_id_of_flag):
                    self.MySQL_DataBase.set_important_dp_weight_Function(MPL_id_of_flag, 0)
            else:
                print_and_logging_Function("error", f"No valid result fetched from the {flag_id} flag", "title")

            db_cursor.close()  # ✅ Close cursor after use

        except Exception as e:
            print_and_logging_Function("error", f"Error retrieving data for row {flag_id}: {e}", "title")

CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]