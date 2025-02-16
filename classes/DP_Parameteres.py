from dataclasses import dataclass
import typing

from .FlagPoint import FlagPoint

@dataclass
class DP_Parameteres:  
    High: FlagPoint 
    Low: FlagPoint
    type: typing.Literal["FTC", "EL", "MPL"] = "FTC"
    weight: int = 0
    start_index : int = -1