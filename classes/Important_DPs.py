import sys
import os
import typing
import pandas as pd
import numpy as np

# Dynamically add the top-level package directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the required modules
from functions.logger import The_logger
from classes.DP_Parameteres import DP_Parameteres_Class
from classes.FlagPoint import FlagPoint_Class

class Important_DPs_Class:
    def __init__(self, 
                 dataset: pd.DataFrame, 
                 direction: typing.Literal["Bullish", "Bearish", "Undefined"], 
                 flag_id: pd.Series,
                 start_of_index: int):

        The_logger.info(f"Detecting Important DPs of Flag {flag_id}")
        highs = dataset['high'].to_numpy()
        lows = dataset['low'].to_numpy()
        local_Lows_index = np.where(dataset['is_local_min'].to_numpy())[0]
        local_Highs_index = np.where(dataset['is_local_max'].to_numpy())[0]
        time = dataset['time']

        self.DP = self.DP_Detector_Function(lows, highs, time, direction, flag_id, local_Lows_index, local_Highs_index, start_of_index)

    def DP_Detector_Function(self, 
                    lows: np.ndarray, 
                    highs: np.ndarray, 
                    time,
                    flag_type: typing.Literal["Bullish", "Bearish", "Undefined"], 
                    flag_id: pd.Series,  
                    local_Lows_index: np.ndarray, 
                    local_Highs_index: np.ndarray,
                    start_of_index: int):
        
        DP = DP_Parameteres_Class(FlagPoint_Class(None, None,None), FlagPoint_Class(None, None,None))
        if flag_type == "Bullish":
            if len(local_Lows_index) == 0:
                DP.weight = 0
                return DP
            local_Lows = lows[local_Lows_index]
            low_of_DP = local_Lows.min()
            low_of_DP_index = local_Lows_index[np.where(local_Lows == low_of_DP)[0][-1]]
            DP.Low.index = low_of_DP_index + start_of_index
            DP.Low.time = time[DP.Low.index]
            DP.Low.price = low_of_DP
            
            highs_slice = highs[low_of_DP_index+1:]
            if highs_slice.size > 0:
                high_of_DP = highs_slice.max()
                high_of_DP_index = (low_of_DP_index+1) + np.where(highs_slice == high_of_DP)[0][-1]
                DP.High.index = high_of_DP_index + start_of_index
                DP.High.time = time[DP.High.index]
                DP.High.price = high_of_DP
                DP.weight = 1
            else:
                DP.weight = 0
        elif flag_type == "Bearish":
            if len(local_Highs_index) == 0:
                DP.weight = 0
                return DP
            local_highs = highs[local_Highs_index]
            high_of_DP = local_highs.max()
            high_of_DP_index = local_Highs_index[np.where(local_highs == high_of_DP)[0][-1]]
            DP.High.index = high_of_DP_index + start_of_index
            DP.High.time = time[DP.High.index]
            DP.High.price = high_of_DP

            lows_slice = lows[high_of_DP_index+1:]
            if lows_slice.size > 0:
                low_of_DP = lows_slice.min()
                low_of_DP_index = (high_of_DP_index+1) + np.where(lows_slice == low_of_DP)[0][-1]
                DP.Low.index = low_of_DP_index + start_of_index
                DP.Low.time = time[DP.Low.index]
                DP.Low.price = low_of_DP
                DP.weight = 1
            else:
                DP.weight = 0
        return DP

    def __repr__(self):
        return f"Dp: {self.DP}"
