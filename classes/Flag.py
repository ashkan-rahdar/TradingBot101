import typing
import pandas as pd
import numpy as np
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.FlagPoint import FlagPoint
from classes.Important_DPs import Important_DPs
from functions.logger import logger


# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

class Flag:
    def __init__(self, 
                 flag_id: pd.Series, 
                 flag_type: typing.Literal["Bullish", "Bearish","Undefined"], 
                 high: FlagPoint, 
                 low: FlagPoint, 
                 data_in_flag: pd.DataFrame, 
                 start_index: int, 
                 end_index: int, 
                 start_FTC: int,
                 start_EL: int):
        
        self.flag_id = flag_id
        self.flag_type: typing.Literal["Bullish", "Bearish","Undefined"] = flag_type
        self.high = high
        self.low = low
        self.duration = end_index - (low.index if flag_type == "Bearish" else high.index)
        self.Start_index = start_index
        self.End_index = end_index
        self.End_time = data_in_flag['time'][end_index]
        self.Start_time = data_in_flag['time'][start_index]

        self.FTC = Important_DPs(
            dataset= (data_in_flag.iloc[high.index - start_index:low.index - start_index] if flag_type=="Bullish" 
                      else data_in_flag.iloc[low.index - start_index:high.index - start_index]),
            direction = self.flag_type,
            flag_id= self.flag_id,
            start_of_index = high.index if flag_type == "Bullish" else low.index
            )
        self.FTC.DP.type = "FTC"
        self.FTC.DP.start_index = start_FTC
        
        if flag_type == "Bullish":
            EL_direction = "Bearish"
        elif flag_type == "Bearish":
            EL_direction = "Bullish"
        else:
            EL_direction = "Undefined"

        self.EL = Important_DPs(
            dataset= (data_in_flag.iloc[:high.index - start_index] if flag_type=="Bullish" 
                      else data_in_flag.iloc[:low.index - start_index]),
            direction = EL_direction,
            flag_id= self.flag_id,
            start_of_index= self.Start_index
        )
        self.EL.DP.type = "EL"
        self.EL.DP.start_index = start_EL
        self.weight = self.weight_of_flag()
        self.status :typing.Literal["Major", "Minor","Undefined"] = "Major"
        
        # self.validate_DP(
        #     Important_DP=self.FTC,
        #     dataset= (data_in_flag.iloc[low.index - start_index + 1:] if flag_type=="Bullish" 
        #               else data_in_flag.iloc[high.index - start_index + 1:]))
        # self.validate_DP(
        #     Important_DP=self.EL,
        #     dataset= (data_in_flag.iloc[low.index - start_index + 1:] if flag_type=="Bullish" 
        #               else data_in_flag.iloc[high.index - start_index + 1:]))
        
    def weight_of_flag(self):
        weights = []
        
        max_weight  = config["trading_configs"]["risk_management"]["max_wieght"] 
        # duration of flag

        if(self.duration / 15 < max_weight): weights.append(self.duration / 15)
        else: weights.append(max_weight)
        
        return sum(weights)
    
    def validate_DP(self, Important_DP: Important_DPs, dataset: pd.DataFrame):
        highs = dataset['high'].to_numpy()
        lows = dataset['low'].to_numpy()
        local_Lows_index = np.where(dataset['is_local_min'].to_numpy())[0]
        local_Highs_index = np.where(dataset['is_local_max'].to_numpy())[0]

        if Important_DP.DP.Status != "Active":
            return

        if self.flag_type == "Bearish":
            if local_Highs_index.size == 0:
                return

            local_Highs = highs[local_Highs_index]
            for high in local_Highs:
                if high < Important_DP.DP.High.price and high > Important_DP.DP.Low.price:
                    index_high = np.where(highs == high)[0][-1]
                    if lows[:index_high].min() <= Important_DP.DP.Low.price:
                        Important_DP.DP.Status = "Used"
                        break

        elif self.flag_type == "Bullish":
            if local_Lows_index.size == 0:
                return

            local_Lows = lows[local_Lows_index]
            for low in local_Lows:
                if low > Important_DP.DP.Low.price and low < Important_DP.DP.High.price:
                    index_low = np.where(lows == low)[0][-1]
                    if highs[:index_low].max() >= Important_DP.DP.High.price:
                        Important_DP.DP.Status = "Used"
                        break
    
    def __repr__(self):
        return (f"Flag is like ID: {self.flag_id}, Type: {self.flag_type}, High: {self.high}, Low: {self.low}, "
                f"Start index: {self.Start_index}, End index: {self.End_index}, EL: {self.EL}, "
                f"Duration: {self.duration}, FTC: {self.FTC}")
    def to_Dataframe(self):
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