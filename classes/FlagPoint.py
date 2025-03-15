from dataclasses import dataclass
import pandas

@dataclass
class FlagPoint_Class:
    price: int
    time: pandas.Timestamp
    index: int = -1