import sys
import os
import typing
import pandas as pd
import numpy as np

# Dynamically add the top-level package directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the required modules
from functions.logger import logger
from classes.DP_Parameteres import DP_Parameteres
from classes.FlagPoint import FlagPoint

class Important_DPs:
    def __init__(self, 
                 dataset: pd.DataFrame, 
                 direction: typing.Literal["Bullish", "Bearish", "Undefined"], 
                 flag_id: pd.Series,
                 start_of_index: int):

        logger.info(f"Detecting Important DPs of Flag {flag_id}")
        highs = dataset['high'].to_numpy()
        lows = dataset['low'].to_numpy()
        local_Lows_index = np.where(dataset['is_local_min'].to_numpy())[0]
        local_Highs_index = np.where(dataset['is_local_max'].to_numpy())[0]

        self.DP = self.DP_Detector(lows, highs, direction, flag_id, local_Lows_index, local_Highs_index, start_of_index)

    def DP_Detector(self, 
                    lows: np.ndarray, 
                    highs: np.ndarray, 
                    flag_type: typing.Literal["Bullish", "Bearish", "Undefined"], 
                    flag_id: pd.Series,  
                    local_Lows_index: np.ndarray, 
                    local_Highs_index: np.ndarray,
                    start_of_index: int):
        
        DP = DP_Parameteres(FlagPoint(None, None), FlagPoint(None, None))
        if flag_type == "Bullish":
            if len(local_Lows_index) == 0:
                logger.warning(f"No valid Tasvie for Flag -> {flag_id}")
                DP.Status = "Not Valid"
                return DP
            local_Lows = lows[local_Lows_index]
            low_of_DP = local_Lows.min()
            low_of_DP_index = local_Lows_index[np.where(local_Lows == low_of_DP)[0][-1]]
            DP.Low.index = low_of_DP_index + start_of_index
            DP.Low.price = low_of_DP
            
            highs_slice = highs[low_of_DP_index+1:]
            if highs_slice.size > 0:
                high_of_DP = highs_slice.max()
                high_of_DP_index = (low_of_DP_index+1) + np.where(highs_slice == high_of_DP)[0][-1]
                DP.High.index = high_of_DP_index + start_of_index
                DP.High.price = high_of_DP
                DP.weight = 1
            else:
                DP.Status = "Not Valid"
                logger.warning(f"No highs found in the range for Flag -> {flag_id}")
        elif flag_type == "Bearish":
            if len(local_Highs_index) == 0:
                logger.warning(f"No valid Tasvie for Flag -> {flag_id}")
                DP.Status = "Not Valid"
                return DP
            local_highs = highs[local_Highs_index]
            high_of_DP = local_highs.max()
            high_of_DP_index = local_Highs_index[np.where(local_highs == high_of_DP)[0][-1]]
            DP.High.index = high_of_DP_index + start_of_index
            DP.High.price = high_of_DP

            lows_slice = lows[high_of_DP_index+1:]
            if lows_slice.size > 0:
                low_of_DP = lows_slice.min()
                low_of_DP_index = (high_of_DP_index+1) + np.where(lows_slice == low_of_DP)[0][-1]
                DP.Low.index = low_of_DP_index + start_of_index
                DP.Low.price = low_of_DP
                DP.weight = 1
            else:
                DP.Status = "Not Valid"
                logger.warning(f"No lows found in the range for Flag -> {flag_id}")
        return DP

    def __repr__(self):
        return f"Dp: {self.DP}"
