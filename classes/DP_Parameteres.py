from dataclasses import dataclass
import typing
import datetime
from .FlagPoint import FlagPoint_Class

@dataclass
class DP_Parameteres_Class:  
    High: FlagPoint_Class 
    Low: FlagPoint_Class
    type: typing.Literal["FTC", "EL", "MPL"] = "FTC"
    weight: int = 0
    first_valid_trade_time : datetime.datetime = datetime.datetime.now()
    trade_direction : typing.Literal["Bullish", "Bearish", "Undefined"] = "Undefined"