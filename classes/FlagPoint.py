from dataclasses import dataclass
import pandas

@dataclass
class FlagPoint_Class:
    price: int
    index: int
    time: pandas.Timestamp