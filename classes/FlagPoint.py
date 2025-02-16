from dataclasses import dataclass
import pandas

@dataclass
class FlagPoint:
    price: int
    index: int
    time: pandas.Timestamp