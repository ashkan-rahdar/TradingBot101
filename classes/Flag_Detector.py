import pandas as pd
import numpy as np
import sys
import os
from colorama import Fore, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag_Class
from functions.logger import The_logger
from classes.FlagPoint import FlagPoint_Class
from classes.Database import Database_Class    

class FlagDetector_Class:
    """Detects Bullish and Bearish flags from a dataset."""
    def __init__(self, The_timeframe:str, The_DataBase: Database_Class):
        self.DataBase = The_DataBase
        self.DB_name_flag_points_table = f"Flag_Points_{The_timeframe}"
        self.DB_name_flags_table = f"Flags_{The_timeframe}"

    def detect_local_extremes_Function(self, The_dataset: pd.DataFrame):
        """Precompute local maxima and minima for the dataset."""
        highs = The_dataset['high']
        lows = The_dataset['low']

        # Using NumPy for vectorized operations
        is_local_max = (highs > np.roll(highs, 1)) & (highs > np.roll(highs, -1))
        is_local_min = (lows < np.roll(lows, 1)) & (lows < np.roll(lows, -1))

        # Assign results back to the dataset
        The_dataset['is_local_max'] = is_local_max
        The_dataset['is_local_min'] = is_local_min

    async def detect_bullish_flags_Function(self, The_dataset: pd.DataFrame):
        """Detect Bullish Flags."""
        The_logger.info("Detecting Bullish Flags...")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT +"Detecting Bullish Flags..." + Style.RESET_ALL)
        highs = The_dataset['high']
        lows = The_dataset['low']

        local_max_indices = np.where(The_dataset['is_local_max'].to_numpy())[0]
        for i in local_max_indices:
            high_of_flag = highs[i]

            # Find end of flag
            end_of_flag_indices = np.where((highs[i + 1:] > high_of_flag))[0] if i+1 < len(lows) else np.array([])
            if end_of_flag_indices.size == 0:
                continue
            end_of_flag_index = i + 1 + end_of_flag_indices[0]

            if end_of_flag_index - i <= 15:
                continue

            # Find low of flag (lowest low between i and end_of_flag_index)
            low_of_flag = lows[i:end_of_flag_index + 1].min()
            low_of_flag_index = i + np.where(lows[i:end_of_flag_index + 1] == low_of_flag)[0][-1]

            # Find start of flag (first low lower than low_of_flag)
            start_of_flag_index = None
            for j in range(1, i):
                if highs[i-j] >= high_of_flag:
                    break
                elif lows[i-j] < low_of_flag:
                    start_of_flag_index = i-j
                    break
            
            if start_of_flag_index is None:
                continue
            
            # checking if is not a minor flag
            minor_indexes = np.where(highs[i+1:end_of_flag_index] > high_of_flag)[0] if i+1 < len(lows) else np.array([])
            if minor_indexes.size > 0:
                if minor_indexes[0] + i + 1 < low_of_flag_index:
                    continue
            
            # finding valid indexes for EL
            start_indices_EL = np.where((highs[i + 1:] > high_of_flag) & (lows[i + 1:] > high_of_flag))[0] if i+1 < len(lows) else np.array([])
            if start_indices_EL.size == 0:
                start_index_EL = None
            else:
                used_flag_indices =  np.where((lows[end_of_flag_index:] < low_of_flag))[0]
                if used_flag_indices.size != 0 and used_flag_indices[0] + end_of_flag_index < start_indices_EL[0] + i + 1:
                    start_index_EL = None
                else:
                    start_index_EL = i + 1 + start_indices_EL[0]
            # Append valid flag
            flag = Flag_Class(
                The_flag_id= The_dataset['time'][i],
                The_flag_type=("Bullish" if low_of_flag_index != i else "Undefined"),
                The_high=FlagPoint_Class(price= high_of_flag,index= i, time=The_dataset["time"][i]),
                The_low=FlagPoint_Class(price= low_of_flag, index= low_of_flag_index, time= The_dataset["time"][low_of_flag_index]),
                The_data_in_flag= The_dataset.iloc[start_of_flag_index:end_of_flag_index + 1],
                The_start_index= start_of_flag_index,
                The_end_index= end_of_flag_index,
                The_start_FTC= end_of_flag_index,
                The_start_EL= start_index_EL
            )
            await self.add_flag_Function(flag)
    async def detect_bearish_flags_Function(self, The_dataset: pd.DataFrame):
        """Detect Bearish Flags."""
        The_logger.info("Detecting Bearish Flags...")
        print(Fore.LIGHTRED_EX + Style.BRIGHT +"Detecting Bearish Flags..." + Style.RESET_ALL)
        highs = The_dataset['high']
        lows = The_dataset['low']

        local_min_indices = np.where(The_dataset['is_local_min'].to_numpy())[0]
        for i in local_min_indices:
            low_of_flag = lows[i]

            # Find end of flag
            end_of_flag_indices = np.where((lows[i + 1:] < low_of_flag))[0] if i+1 < len(lows) else np.array([])
            if end_of_flag_indices.size == 0:
                continue
            end_of_flag_index = i + 1 + end_of_flag_indices[0]

            if end_of_flag_index - i <= 15:
                continue

            # Find high of flag (highest high between i and end_of_flag_index)
            high_of_flag = highs[i:end_of_flag_index + 1].max()
            high_of_flag_index = i + np.where(highs[i:end_of_flag_index + 1] == high_of_flag)[0][-1]

            # Find start of flag (first high lower than high_of_flag)
            start_of_flag_index = None
            for j in range(1, i):
                if lows[i-j] <= low_of_flag:
                    break
                elif highs[i-j] > high_of_flag:
                    start_of_flag_index = i-j
                    break
            
            if start_of_flag_index is None:
                continue

            # checking if is not a minor flag
            minor_indexes = np.where(lows[i+1:end_of_flag_index] < low_of_flag)[0] if i+1 < len(lows) else np.array([])
            if minor_indexes.size > 0:
                if minor_indexes[0] + i + 1 < high_of_flag_index:
                    continue  
            
            # finding valid indexes for EL
            start_indices_EL = np.where((lows[i + 1:] < low_of_flag) & (highs[i + 1:] < low_of_flag))[0] if i+1 < len(lows) else np.array([])
            if start_indices_EL.size == 0:
                start_index_EL = None
            else:
                used_flag_indices =  np.where((highs[end_of_flag_index:] > high_of_flag))[0]
                if used_flag_indices.size != 0 and used_flag_indices[0] + end_of_flag_index < start_indices_EL[0] + i + 1:
                    start_index_EL = None
                else:
                    start_index_EL = i + 1 + start_indices_EL[0]

            # Append valid flag
            flag = Flag_Class(
                The_flag_id= The_dataset['time'][i],
                The_flag_type= ("Bearish" if high_of_flag_index != i else "Undefined"),
                The_high=FlagPoint_Class(price= high_of_flag, index= high_of_flag_index, time= The_dataset["time"][high_of_flag_index]),
                The_low=FlagPoint_Class(price= low_of_flag, index= i, time= The_dataset["time"][i]),
                The_data_in_flag= The_dataset.iloc[start_of_flag_index:end_of_flag_index + 1],
                The_start_index= start_of_flag_index,
                The_end_index= end_of_flag_index,
                The_start_FTC= end_of_flag_index,
                The_start_EL= start_index_EL
            )
            await self.add_flag_Function(flag)
            
    async def run_detection_Function(self, The_dataset: pd.DataFrame):
        """Run flag detection for both Bullish and Bearish flags."""
        try:
            self.detect_local_extremes_Function(The_dataset)  # Precompute local extremes
            await self.detect_bullish_flags_Function(The_dataset)
            await self.detect_bearish_flags_Function(The_dataset)
            The_logger.info("|||||||||||||| Detection complete ||||||||||||||||||")
            print(Fore.GREEN + Style.BRIGHT + "|||||||||||||| Detection complete ||||||||||||||||||" + Style.RESET_ALL)
        except Exception as e:
            The_logger.error(f"An error occurred during detection: {e}")
            raise

    async def add_flag_Function(self, The_flag: Flag_Class):
        try:
            # Check if flag already exists in the database
            self.DataBase.cursor.execute(f"SELECT COUNT(*) FROM {self.DB_name_flags_table} WHERE Starting_time = %s", (The_flag.Start_time,))
            exists = self.DataBase.cursor.fetchone()[0] > 0

            if exists:
                return  # Don't insert duplicate flags

            # Insert new flag into the database
            await self.DataBase.save_data_Function(The_flag)  

        except Exception as e:
            The_logger.critical(f"Error in adding flag {The_flag.flag_id} to DB: {e}")