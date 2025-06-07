import typing
import pandas as pd
from pandas import Series
import numpy as np
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.FlagPoint import FlagPoint_Class
from classes.DP_Parameteres import DP_Parameteres_Class
from functions.logger import print_and_logging_Function


# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

class Flag_Class:
    """
    Flag_Class is a representation of a trading flag pattern, which is a technical analysis concept used in trading. 
    This class encapsulates the properties and methods required to define, analyze, and validate a flag pattern.
    Attributes:
        flag_type (Literal["Bullish", "Bearish", "Undefined"]): The type of the flag pattern.
        high (FlagPoint_Class): The high point of the flag.
        low (FlagPoint_Class): The low point of the flag.
        duration (int): The duration of the flag pattern.
        Start_index (int): The starting index of the flag in the dataset.
        End_index (int): The ending index of the flag in the dataset.
        End_time (Any): The ending time of the flag pattern.
        Start_time (Any): The starting time of the flag pattern.
        Unique_point (Any): The unique point of the flag, determined by the flag type.
        FTC (DP_Parameteres_Class): The first trade confirmation (FTC) parameters.
        EL (DP_Parameteres_Class): The entry level (EL) parameters.
        weight (float): The weight of the flag pattern.
        status (Literal["Major", "Minor", "Undefined"]): The status of the flag pattern.
        MPL (DP_Parameteres_Class): The most probable level (MPL) parameters.
    """
    
    def __init__(self,  
                 The_flag_type: typing.Literal["Bullish", "Bearish","Undefined"], 
                 The_high: FlagPoint_Class, 
                 The_low: FlagPoint_Class, 
                 The_data_in_flag: pd.DataFrame, 
                 The_start_index: int, 
                 The_end_index: int):
        """        
        __init__(self, The_flag_type, The_high, The_low, The_data_in_flag, The_start_index, The_end_index, The_start_FTC):
            Initializes the Flag_Class object with the given parameters.
            Args:
                The_flag_type (Literal["Bullish", "Bearish", "Undefined"]): The type of the flag pattern.
                The_high (FlagPoint_Class): The high point of the flag.
                The_low (FlagPoint_Class): The low point of the flag.
                The_data_in_flag (pd.DataFrame): The dataset containing the flag data.
                The_start_index (int): The starting index of the flag in the dataset.
                The_end_index (int): The ending index of the flag in the dataset.
                The_start_FTC (int): The starting index for the first trade confirmation.
        """
        try:
            self.flag_type: typing.Literal["Bullish", "Bearish","Undefined"] = The_flag_type
            self.high = The_high
            self.low = The_low
            self.length = The_end_index - (The_low.index if The_flag_type == "Bearish" else The_high.index)
            self.Start_index = The_start_index
            self.End_index = The_end_index
            self.End_time = The_data_in_flag['time'][The_end_index]
            self.Start_time = The_data_in_flag['time'][The_start_index]
            self.Unique_point = The_high.time if self.flag_type == "Bullish" else The_low.time

            self.FTC = self.DP_Detector_Function(
                                                dataset = (The_data_in_flag.iloc[The_high.index - The_start_index : The_low.index - The_start_index + 1] if The_flag_type=="Bullish" 
                                                        else The_data_in_flag.iloc[The_low.index - The_start_index : The_high.index - The_start_index + 1]),
                                                flag_type = self.flag_type,
                                                start_of_index = The_high.index if The_flag_type == "Bullish" else The_low.index)
            self.FTC.type = "FTC"
            
            if The_flag_type == "Bullish":
                EL_direction = "Bearish"
            elif The_flag_type == "Bearish":
                EL_direction = "Bullish"
            else:
                EL_direction = "Undefined"

            self.EL = self.DP_Detector_Function(
                                                dataset= (The_data_in_flag.iloc[:The_high.index - The_start_index + 1] if The_flag_type=="Bullish" 
                                                else The_data_in_flag.iloc[:The_low.index - The_start_index + 1]),
                                                flag_type = EL_direction,
                                                start_of_index= self.Start_index)
            self.EL.type = "EL"
            self.status :typing.Literal["Major", "Minor","Undefined"] = "Major"
            

            if The_flag_type == "Bullish":
                self.MPL = DP_Parameteres_Class(self.high, self.EL.High)
                self.MPL.weight = 1
                if self.EL.length is not None:
                    self.MPL.length_cal_Function()
            elif The_flag_type == "Bearish":
                self.MPL = DP_Parameteres_Class(self.EL.Low, self.low)
                self.MPL.weight = 1
                if self.EL.length is not None:
                    self.MPL.length_cal_Function()
            else:
                self.MPL = DP_Parameteres_Class(FlagPoint_Class(None, None, None), FlagPoint_Class(None, None, None)) # type: ignore
            self.MPL.type = "MPL"

            self.FTC.trade_direction = self.EL.trade_direction = self.MPL.trade_direction = self.flag_type
            self.FTC.first_valid_trade_time = self.EL.first_valid_trade_time = self.MPL.first_valid_trade_time = self.End_time
            
            if self.FTC.length is not None:
                self.DP_feature_extraction_Function(self.FTC, 
                                        The_data_in_flag.iloc[self.low.index - The_start_index:] if The_flag_type == "Bullish"
                                        else The_data_in_flag.iloc[self.high.index - The_start_index:])
            if self.EL.length is not None:
                self.DP_feature_extraction_Function(self.EL,
                                        The_data_in_flag.iloc[self.low.index - The_start_index:] if The_flag_type == "Bullish"
                                        else The_data_in_flag.iloc[self.high.index - The_start_index:])
                if self.FTC.length is not None:
                    self.FTC.related_DP_indexes.append(self.EL.ID_generator_Function())
                    self.FTC.related_DP_indexes.append(self.MPL.ID_generator_Function())
                    
                    if self.flag_type == "Bullish":
                        self.FTC.Is_related_DP_used = self.FTC.High.price > self.EL.Low.price
                    else:
                        self.FTC.Is_related_DP_used = self.FTC.Low.price <  self.EL.High.price
                
                self.EL.related_DP_indexes.append(self.MPL.ID_generator_Function())
            if self.MPL.length is not None:
                self.DP_feature_extraction_Function(self.MPL,
                                        The_data_in_flag.iloc[self.low.index - The_start_index:] if The_flag_type == "Bullish"
                                        else The_data_in_flag.iloc[self.high.index - The_start_index:])
        except Exception as e:
            print_and_logging_Function("error", f"Error in creating the {self.Unique_point} flag: {e}", "title")
            
    def DP_Detector_Function(self, 
                            dataset: pd.DataFrame,            
                            flag_type: typing.Literal["Bullish", "Bearish", "Undefined"],   
                            start_of_index: int) -> DP_Parameteres_Class:
        """ Detects the important data points (DP) for the flag pattern.
            Args:
                dataset (pd.DataFrame): The dataset containing the flag data.
                flag_type (Literal["Bullish", "Bearish", "Undefined"]): The type of the flag pattern.
                start_of_index (int): The starting index for the detection.
            Returns:
                DP_Parameteres_Class: The detected data points for the flag pattern.
        """
        time : Series[pd.Timestamp] = dataset['time']

        DP = DP_Parameteres_Class(FlagPoint_Class(None, None,None), FlagPoint_Class(None, None,None)) # type: ignore
        if flag_type == "Bullish":
            highs = dataset['high'].to_numpy()
            dataprime = dataset.iloc[:-1]
            lows = dataprime['low'].to_numpy()
            local_Lows_index = np.where(dataprime['is_local_min'].to_numpy())[0] 
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
                DP.length_cal_Function()
            else:
                DP.weight = 0
        elif flag_type == "Bearish":
            lows = dataset['low'].to_numpy()
            dataprime = dataset.iloc[:-1]
            highs = dataprime['high'].to_numpy()
            local_Highs_index = np.where(dataprime['is_local_max'].to_numpy())[0] 

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
                DP.length_cal_Function()
            else:
                DP.weight = 0
        return DP
    
    def DP_feature_extraction_Function(self, aDP: DP_Parameteres_Class, Dataset: pd.DataFrame):
        if aDP.trade_direction == "Bullish":
            mask = (Dataset['low'] >= aDP.Low.price) & (Dataset['low'] <= aDP.High.price)
            filtered_lows = Dataset['low'][mask]
            aDP.number_used_candle = len(filtered_lows)
            if not filtered_lows.empty:
                aDP.used_ratio = (aDP.High.price - filtered_lows.min()) / (aDP.High.price - aDP.Low.price)
                aDP.Is_used_half = aDP.used_ratio >= 0.5
                aDP.Is_golfed =  aDP.Is_golfed >= 1
        elif aDP.trade_direction == "Bearish":
            mask = (Dataset['high'] >= aDP.Low.price) & (Dataset['high'] <= aDP.High.price)
            filtered_highs = Dataset['high'][mask]
            aDP.number_used_candle = len(filtered_highs)
            if not filtered_highs.empty:
                aDP.used_ratio = (filtered_highs.max() - aDP.Low.price) / (aDP.High.price - aDP.Low.price)
                aDP.Is_used_half = aDP.used_ratio >= 0.5
                aDP.Is_golfed =  aDP.Is_golfed >= 1
                
        aDP.ratio_to_flag = (aDP.High.price - aDP.Low.price) / (self.high.price - self.low.price)
        aDP.parent_length = self.length
        return
    
    def __repr__(self):
        return (f"The Detected Flag: Type: {self.flag_type}, High: {self.high}, Low: {self.low}, "
                f"Start index: {self.Start_index}, End index: {self.End_index}, EL: {self.EL}, "
                f"Duration: {self.length}, FTC: {self.FTC}")