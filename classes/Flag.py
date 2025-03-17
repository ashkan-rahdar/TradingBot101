import typing
import pandas as pd
import numpy as np
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.FlagPoint import FlagPoint_Class
from functions.logger import print_and_logging_Function
from classes.DP_Parameteres import DP_Parameteres_Class


# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

class Flag_Class:
    def __init__(self,  
                 The_flag_type: typing.Literal["Bullish", "Bearish","Undefined"], 
                 The_high: FlagPoint_Class, 
                 The_low: FlagPoint_Class, 
                 The_data_in_flag: pd.DataFrame, 
                 The_start_index: int, 
                 The_end_index: int, 
                 The_start_FTC: int):

        self.flag_type: typing.Literal["Bullish", "Bearish","Undefined"] = The_flag_type
        self.high = The_high
        self.low = The_low
        self.duration = The_end_index - (The_low.index if The_flag_type == "Bearish" else The_high.index)
        self.Start_index = The_start_index
        self.End_index = The_end_index
        self.End_time = The_data_in_flag['time'][The_end_index]
        self.Start_time = The_data_in_flag['time'][The_start_index]
        self.Unique_point = The_high.time if self.flag_type == "Bullish" else The_low.time

        self.FTC = self.DP_Detector_Function(
                                            dataset = (The_data_in_flag.iloc[The_high.index - The_start_index:The_low.index - The_start_index] if The_flag_type=="Bullish" 
                                                    else The_data_in_flag.iloc[The_low.index - The_start_index:The_high.index - The_start_index]),
                                            flag_type = self.flag_type,
                                            start_of_index = The_high.index if The_flag_type == "Bullish" else The_low.index)
        self.FTC.type = "FTC"
        self.FTC.first_valid_trade_time = The_start_FTC
        
        if The_flag_type == "Bullish":
            EL_direction = "Bearish"
        elif The_flag_type == "Bearish":
            EL_direction = "Bullish"
        else:
            EL_direction = "Undefined"

        self.EL = self.DP_Detector_Function(
                                            dataset= (The_data_in_flag.iloc[:The_high.index - The_start_index] if The_flag_type=="Bullish" 
                                            else The_data_in_flag.iloc[:The_low.index - The_start_index]),
                                            flag_type = EL_direction,
                                            start_of_index= self.Start_index)
        self.EL.type = "EL"
        self.weight = self.weight_of_flag_Function()
        self.status :typing.Literal["Major", "Minor","Undefined"] = "Major"
        

        if The_flag_type == "Bullish":
            self.MPL = DP_Parameteres_Class(self.high, self.EL.High)
            self.MPL.weight = 1
        elif The_flag_type == "Bearish":
            self.MPL = DP_Parameteres_Class(self.EL.Low, self.low)
            self.MPL.weight = 1
        else:
            self.MPL = DP_Parameteres_Class(FlagPoint_Class(None, None, None), FlagPoint_Class(None, None, None))
        self.MPL.type = "MPL"

        self.FTC.trade_direction = self.EL.trade_direction = self.MPL.trade_direction = self.flag_type
        self.FTC.first_valid_trade_time = self.EL.first_valid_trade_time = self.MPL.first_valid_trade_time = self.End_time
        
    def DP_Detector_Function(self, 
                            dataset: pd.DataFrame,            
                            flag_type: typing.Literal["Bullish", "Bearish", "Undefined"],   
                            start_of_index: int) -> DP_Parameteres_Class:
        
        highs = dataset['high'].to_numpy()
        lows = dataset['low'].to_numpy()
        local_Lows_index = np.where(dataset['is_local_min'].to_numpy())[0]
        local_Highs_index = np.where(dataset['is_local_max'].to_numpy())[0]
        time = dataset['time']

        time = dataset['time']
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
    
    def weight_of_flag_Function(self):
        weights = []
        
        max_weight  = config["trading_configs"]["risk_management"]["max_wieght"] 
        # duration of flag

        if(self.duration / 15 < max_weight): weights.append(self.duration / 15)
        else: weights.append(max_weight)
        
        return sum(weights)
    
    def validate_DP_Function(self, The_Important_DP: DP_Parameteres_Class, The_dataset: pd.DataFrame):
        highs = The_dataset['high'].to_numpy()
        lows = The_dataset['low'].to_numpy()
        local_Lows_index = np.where(The_dataset['is_local_min'].to_numpy())[0]
        local_Highs_index = np.where(The_dataset['is_local_max'].to_numpy())[0]

        if The_Important_DP.weight != 1:
            return

        if self.flag_type == "Bearish":
            if local_Highs_index.size == 0:
                return

            local_Highs = highs[local_Highs_index]
            for high in local_Highs:
                if high < The_Important_DP.High.price and high > The_Important_DP.Low.price:
                    index_high = np.where(highs == high)[0][-1]
                    if lows[:index_high].min() <= The_Important_DP.Low.price:
                        The_Important_DP.weight = 0
                        break

        elif self.flag_type == "Bullish":
            if local_Lows_index.size == 0:
                return

            local_Lows = lows[local_Lows_index]
            for low in local_Lows:
                if low > The_Important_DP.Low.price and low < The_Important_DP.High.price:
                    index_low = np.where(lows == low)[0][-1]
                    if highs[:index_low].max() >= The_Important_DP.High.price:
                        The_Important_DP.weight = 0
                        break
    
    def __repr__(self):
        return (f"The Detected Flag: Type: {self.flag_type}, High: {self.high}, Low: {self.low}, "
                f"Start index: {self.Start_index}, End index: {self.End_index}, EL: {self.EL}, "
                f"Duration: {self.duration}, FTC: {self.FTC}")