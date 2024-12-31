import typing
import pandas as pd
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.FlagPoint import FlagPoint
from classes.Important_DPs import Important_DPs



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
        self.flag_type = flag_type
        self.high = high
        self.low = low
        self.duration = end_index - (low.index if flag_type == "Bearish" else high.index)
        self.Start_index = start_index
        self.End_index = end_index

        self.FTC = Important_DPs(
            dataset= (data_in_flag.iloc[high.index - start_index:low.index - start_index] if flag_type=="Bullish" 
                      else data_in_flag.iloc[low.index - start_index:high.index - start_index]),
            direction = self.flag_type,
            flag_id= self.flag_id,
            start_of_index = high.index if flag_type == "Bullish" else low.index
            )
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

        self.EL.DP.start_index = start_EL
        self.weight = self.weight_of_flag()

    def weight_of_flag(self):
        weights = []
        
        max_weight  = config["trading_configs"]["risk_management"]["max_wieght"] 
        # duration of flag

        if(self.duration / 15 < max_weight): weights.append(self.duration / 15)
        else: weights.append(max_weight)
        
        return sum(weights)
    def __repr__(self):
        return (f"Flag is like ID: {self.flag_id}, Type: {self.flag_type}, High: {self.high}, Low: {self.low}, "
                f"Start index: {self.Start_index}, End index: {self.End_index}, EL: {self.EL}, "
                f"Duration: {self.duration}, FTC: {self.FTC}")