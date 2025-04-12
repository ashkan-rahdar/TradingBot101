import typing
import datetime
import pandas as pd
from .FlagPoint import FlagPoint_Class

class DP_Parameteres_Class:
    def __init__(self, 
                High: FlagPoint_Class, 
                Low: FlagPoint_Class,
                type: typing.Literal["FTC", "EL", "MPL"] = "FTC",
                weight: int = 0,
                first_valid_trade_time : datetime.datetime = datetime.datetime.now(),
                trade_direction : typing.Literal["Bullish", "Bearish", "Undefined"] = "Undefined"):
        self.High = High
        self.Low = Low
        self.type = type
        self.weight = weight
        self.first_valid_trade_time =  first_valid_trade_time
        self.trade_direction = trade_direction

        # if self.High != None and self.Low != None and self.High.time != None and self.Low.time != None:
        #     self.length = int(abs(self.High.time - self.Low.time)/ pd.Timedelta("1min"))
        # self.ratio_to_flag = 1
        # self.number_used_candle = 0

        self.ID_generator_Function()

    def ID_generator_Function(self):
        if self.High != None and self.Low != None and self.High.time != None and self.Low.time != None:
            self.id = f"H {self.High.time} & L {self.Low.time}"
        else:
            self.id = None
        return self.id
    
    def __repr__(self):
        return (f"DP_Parameteres_Class(type={self.type}, High={self.High}, Low={self.Low}, "
                f"weight={self.weight}, first_valid_trade_time={self.first_valid_trade_time}, "
                f"trade_direction={self.trade_direction})")