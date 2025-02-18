from dataclasses import dataclass
import typing

from .FlagPoint import FlagPoint_Class

@dataclass
class DP_Parameteres_Class:  
    High: FlagPoint_Class 
    Low: FlagPoint_Class
    type: typing.Literal["FTC", "EL", "MPL"] = "FTC"
    weight: int = 0
    start_index : int = -1