import typing
import pandas as pd
import numpy as np
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.FlagPoint import FlagPoint_Class
from classes.Important_DPs import Important_DPs_Class
from functions.logger import The_logger


# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

class Flag_Class:
    def __init__(self, 
                 The_flag_id: pd.Series, 
                 The_flag_type: typing.Literal["Bullish", "Bearish","Undefined"], 
                 The_high: FlagPoint_Class, 
                 The_low: FlagPoint_Class, 
                 The_data_in_flag: pd.DataFrame, 
                 The_start_index: int, 
                 The_end_index: int, 
                 The_start_FTC: int,
                 The_start_EL: int):
        
        self.flag_id = The_flag_id
        self.flag_type: typing.Literal["Bullish", "Bearish","Undefined"] = The_flag_type
        self.high = The_high
        self.low = The_low
        self.duration = The_end_index - (The_low.index if The_flag_type == "Bearish" else The_high.index)
        self.Start_index = The_start_index
        self.End_index = The_end_index
        self.End_time = The_data_in_flag['time'][The_end_index]
        self.Start_time = The_data_in_flag['time'][The_start_index]

        self.FTC = Important_DPs_Class(
            dataset= (The_data_in_flag.iloc[The_high.index - The_start_index:The_low.index - The_start_index] if The_flag_type=="Bullish" 
                      else The_data_in_flag.iloc[The_low.index - The_start_index:The_high.index - The_start_index]),
            direction = self.flag_type,
            flag_id= self.flag_id,
            start_of_index = The_high.index if The_flag_type == "Bullish" else The_low.index
            )
        self.FTC.DP.type = "FTC"
        self.FTC.DP.start_index = The_start_FTC
        
        if The_flag_type == "Bullish":
            EL_direction = "Bearish"
        elif The_flag_type == "Bearish":
            EL_direction = "Bullish"
        else:
            EL_direction = "Undefined"

        self.EL = Important_DPs_Class(
            dataset= (The_data_in_flag.iloc[:The_high.index - The_start_index] if The_flag_type=="Bullish" 
                      else The_data_in_flag.iloc[:The_low.index - The_start_index]),
            direction = EL_direction,
            flag_id= self.flag_id,
            start_of_index= self.Start_index
        )
        self.EL.DP.type = "EL"
        self.EL.DP.start_index = The_start_EL
        self.weight = self.weight_of_flag_Function()
        self.status :typing.Literal["Major", "Minor","Undefined"] = "Major"
        
        # self.validate_DP(
        #     Important_DP=self.FTC,
        #     dataset= (data_in_flag.iloc[low.index - start_index + 1:] if flag_type=="Bullish" 
        #               else data_in_flag.iloc[high.index - start_index + 1:]))
        # self.validate_DP(
        #     Important_DP=self.EL,
        #     dataset= (data_in_flag.iloc[low.index - start_index + 1:] if flag_type=="Bullish" 
        #               else data_in_flag.iloc[high.index - start_index + 1:]))
        
    def weight_of_flag_Function(self):
        weights = []
        
        max_weight  = config["trading_configs"]["risk_management"]["max_wieght"] 
        # duration of flag

        if(self.duration / 15 < max_weight): weights.append(self.duration / 15)
        else: weights.append(max_weight)
        
        return sum(weights)
    
    def validate_DP_Function(self, The_Important_DP: Important_DPs_Class, The_dataset: pd.DataFrame):
        highs = The_dataset['high'].to_numpy()
        lows = The_dataset['low'].to_numpy()
        local_Lows_index = np.where(The_dataset['is_local_min'].to_numpy())[0]
        local_Highs_index = np.where(The_dataset['is_local_max'].to_numpy())[0]

        if The_Important_DP.DP.Status != "Active":
            return

        if self.flag_type == "Bearish":
            if local_Highs_index.size == 0:
                return

            local_Highs = highs[local_Highs_index]
            for high in local_Highs:
                if high < The_Important_DP.DP.High.price and high > The_Important_DP.DP.Low.price:
                    index_high = np.where(highs == high)[0][-1]
                    if lows[:index_high].min() <= The_Important_DP.DP.Low.price:
                        The_Important_DP.DP.Status = "Used"
                        break

        elif self.flag_type == "Bullish":
            if local_Lows_index.size == 0:
                return

            local_Lows = lows[local_Lows_index]
            for low in local_Lows:
                if low > The_Important_DP.DP.Low.price and low < The_Important_DP.DP.High.price:
                    index_low = np.where(lows == low)[0][-1]
                    if highs[:index_low].max() >= The_Important_DP.DP.High.price:
                        The_Important_DP.DP.Status = "Used"
                        break
    
    def __repr__(self):
        return (f"Flag is like ID: {self.flag_id}, Type: {self.flag_type}, High: {self.high}, Low: {self.low}, "
                f"Start index: {self.Start_index}, End index: {self.End_index}, EL: {self.EL}, "
                f"Duration: {self.duration}, FTC: {self.FTC}")
    def to_Dataframe_Function(self):
        data = {
            "Flag ID": [self.flag_id],
            "Type": [self.flag_type],
            "Status": [self.status],
            "High": [self.high],
            "Low": [self.low],
            "Start Time": [self.Start_time],
            "End Time": [self.End_time],
            "EL": [self.EL],
            "Duration": [self.duration],
            "Weight": [self.weight],
            "FTC": [self.FTC],
            "Reaction to FTC": 0, 
            "Reaction to EL": 0
        }
        return pd.DataFrame(data)