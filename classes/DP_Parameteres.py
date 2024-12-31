from dataclasses import dataclass
import typing

from .FlagPoint import FlagPoint

@dataclass
class DP_Parameteres:  
    High: FlagPoint 
    Low: FlagPoint
    Status: typing.Literal["Used", "Active", "Not Valid"] = "Active"
    weight: int = 0
    start_index : int = -1