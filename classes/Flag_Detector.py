import pandas as pd
import numpy as np
import sys
import os
from colorama import Fore, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag
from functions.logger import logger
from classes.FlagPoint import FlagPoint

class FlagDetector:
    """Detects Bullish and Bearish flags from a dataset."""
    def __init__(self):
        self.flags = {} 

    def detect_local_extremes(self, dataset: pd.DataFrame):
        """Precompute local maxima and minima for the dataset."""
        highs = dataset['high']
        lows = dataset['low']

        # Using NumPy for vectorized operations
        is_local_max = (highs > np.roll(highs, 1)) & (highs > np.roll(highs, -1))
        is_local_min = (lows < np.roll(lows, 1)) & (lows < np.roll(lows, -1))

        # Assign results back to the dataset
        dataset['is_local_max'] = is_local_max
        dataset['is_local_min'] = is_local_min

    async def detect_bullish_flags(self, dataset: pd.DataFrame):
        """Detect Bullish Flags."""
        logger.info("Detecting Bullish Flags...")
        print(Fore.BLUE + Style.DIM +"Detecting Bullish Flags..." + Style.RESET_ALL)
        highs = dataset['high']
        lows = dataset['low']

        local_max_indices = np.where(dataset['is_local_max'].to_numpy())[0]
        for i in local_max_indices:
            high_of_flag = highs[i]

            # Find end of flag
            #end_of_flag_indices = np.where((highs[i + 1:] > high_of_flag) & (lows[i + 1:] > high_of_flag))[0] if i+1 < len(lows) else np.array([])
            end_of_flag_indices = np.where((highs[i + 1:] > high_of_flag))[0] if i+1 < len(lows) else np.array([])
            if end_of_flag_indices.size == 0:
                logger.warning(f"No valid end for suspected Bullish Flag starting at index {i}. Skipping.")
                continue
            end_of_flag_index = i + 1 + end_of_flag_indices[0]

            if end_of_flag_index - i <= 15:
                logger.warning(f"Suspected Bullish Flag at index {i} is too short. Skipping.")
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
                logger.warning(f"No valid start point for suspected Bullish Flag starting at index {i}. Skipping.")
                continue
            
            # checking if is not a minor flag
            minor_indexes = np.where(highs[i+1:end_of_flag_index] > high_of_flag)[0] if i+1 < len(lows) else np.array([])
            if minor_indexes.size > 0:
                if minor_indexes[0] + i + 1 < low_of_flag_index:
                    logger.warning(f"Flag starting at index {i} is a minor flag. Skipping...")
                    continue
            
            # finding valid indexes for EL
            start_indices_EL = np.where((highs[i + 1:] > high_of_flag) & (lows[i + 1:] > high_of_flag))[0] if i+1 < len(lows) else np.array([])
            if start_indices_EL.size == 0:
                logger.warning(f"No valid start index for EL DP for suspected Bullish Flag starting at index {i}")
                start_index_EL = None
            else:
                used_flag_indices =  np.where((lows[end_of_flag_index:] < low_of_flag))[0]
                if used_flag_indices.size != 0 and used_flag_indices[0] + end_of_flag_index < start_indices_EL[0] + i + 1:
                    logger.warning(f"No valid start index in valid range for EL DP for suspected Bullish Flag starting at index {i}")
                    start_index_EL = None
                else:
                    start_index_EL = i + 1 + start_indices_EL[0]
            # Append valid flag
            flag = Flag(
                flag_id= dataset['time'][i],
                flag_type=("Bullish" if low_of_flag_index != i else "Undefined"),
                high=FlagPoint(price= high_of_flag,index= i),
                low=FlagPoint(price= low_of_flag, index= low_of_flag_index),
                data_in_flag= dataset.iloc[start_of_flag_index:end_of_flag_index + 1],
                start_index= start_of_flag_index,
                end_index= end_of_flag_index,
                start_FTC= end_of_flag_index,
                start_EL= start_index_EL
            )
            await self.add_flag(flag)
    async def detect_bearish_flags(self, dataset: pd.DataFrame):
        """Detect Bearish Flags."""
        logger.info("Detecting Bearish Flags...")
        print(Fore.BLUE + Style.DIM +"Detecting Bearish Flags..." + Style.RESET_ALL)
        highs = dataset['high']
        lows = dataset['low']

        local_min_indices = np.where(dataset['is_local_min'].to_numpy())[0]
        for i in local_min_indices:
            low_of_flag = lows[i]

            # Find end of flag
            #end_of_flag_indices = np.where((lows[i + 1:] < low_of_flag) & (highs[i + 1:] < low_of_flag))[0] if i+1 < len(lows) else np.array([])
            end_of_flag_indices = np.where((lows[i + 1:] < low_of_flag))[0] if i+1 < len(lows) else np.array([])
            if end_of_flag_indices.size == 0:
                logger.warning(f"No valid end for suspected Bearish Flag starting at index {i}. Skipping.")
                continue
            end_of_flag_index = i + 1 + end_of_flag_indices[0]

            if end_of_flag_index - i <= 15:
                logger.warning(f"Suspected Bearish Flag at index {i} is too short. Skipping.")
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
                logger.warning(f"No valid start point for suspected Bearish Flag starting at index {i}. Skipping.")
                continue

            # checking if is not a minor flag
            minor_indexes = np.where(lows[i+1:end_of_flag_index] < low_of_flag)[0] if i+1 < len(lows) else np.array([])
            if minor_indexes.size > 0:
                if minor_indexes[0] + i + 1 < high_of_flag_index:
                    logger.warning(f"Flag starting at index {i} is a minor flag so we are going to skip it")
                    continue  
            
            # finding valid indexes for EL
            start_indices_EL = np.where((lows[i + 1:] < low_of_flag) & (highs[i + 1:] < low_of_flag))[0] if i+1 < len(lows) else np.array([])
            if start_indices_EL.size == 0:
                logger.warning(f"No valid start index for EL DP for suspected Bearish Flag starting at index {i}")
                start_index_EL = None
            else:
                used_flag_indices =  np.where((highs[end_of_flag_index:] > high_of_flag))[0]
                if used_flag_indices.size != 0 and used_flag_indices[0] + end_of_flag_index < start_indices_EL[0] + i + 1:
                    logger.warning(f"No valid start index in valid range for EL DP for suspected Bearish Flag starting at index {i}")
                    start_index_EL = None
                else:
                    start_index_EL = i + 1 + start_indices_EL[0]

            # Append valid flag
            flag = Flag(
                flag_id= dataset['time'][i],
                flag_type= ("Bearish" if high_of_flag_index != i else "Undefined"),
                high=FlagPoint(price= high_of_flag, index= high_of_flag_index),
                low=FlagPoint(price= low_of_flag, index= i),
                data_in_flag= dataset.iloc[start_of_flag_index:end_of_flag_index + 1],
                start_index= start_of_flag_index,
                end_index= end_of_flag_index,
                start_FTC= end_of_flag_index,
                start_EL= start_index_EL
            )
            await self.add_flag(flag)
            
    async def run_detection(self, dataset: pd.DataFrame):
        """Run flag detection for both Bullish and Bearish flags."""
        try:
            self.detect_local_extremes(dataset)  # Precompute local extremes
            await self.detect_bullish_flags(dataset)
            await self.detect_bearish_flags(dataset)
            logger.info("|||||||||||||| Detection complete ||||||||||||||||||")
            print(Fore.GREEN + Style.BRIGHT + "|||||||||||||| Detection complete ||||||||||||||||||" + Style.RESET_ALL)
        except Exception as e:
            logger.error(f"An error occurred during detection: {e}")
            raise

    async def add_flag(self, flag: Flag):
        if flag.flag_id in self.flags:
            logger.warning(f"Flag {flag.flag_id} already exists. Updating the flag.")
        else:
            logger.info(f"Adding new flag: {flag}")
        self.flags[flag.flag_id] = flag  # Add or update the flag in the dictionary

    def remove_flag(self, flag_id):
        if flag_id not in self.flags:
            logger.error(f"Flag {flag_id} not found. Cannot delete.")
            return
        del self.flags[flag_id]  # Remove the flag from the dictionary
        logger.info(f"Flag {flag_id} removed.")

    def get_flag(self, flag_id):
        if flag_id in self.flags:
            logger.info(f"Retrieved flag {flag_id}: {self.flags[flag_id]}")
            return self.flags[flag_id]
        else:
            logger.warning(f"Flag {flag_id} not found.")
            return None
        


# # Merge new_FLAGS with FLAGS
#     FLAGS = pd.concat([FLAGS, new_FLAGS]).drop_duplicates().reset_index(drop=True)
