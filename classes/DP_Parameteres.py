import typing
import datetime
from .FlagPoint import FlagPoint_Class

class DP_Parameteres_Class:
    """
    DP_Parameteres_Class is a class designed to encapsulate the parameters and attributes 
    associated with a trading bot's decision point (DP). It includes information about 
    high and low flag points, trade type, weight, first valid trade time, and trade direction.
    Attributes:
        High (FlagPoint_Class): The high flag point object, which contains information 
            about the high point in a trade decision.
        Low (FlagPoint_Class): The low flag point object, which contains information 
            about the low point in a trade decision.
        type (Literal["FTC", "EL", "MPL"]): The type of the decision point. Defaults to "FTC".
            - "FTC": First Trade Confirmation
            - "EL": Entry Level
            - "MPL": Mid-Point Level
        weight (int): The weight or significance of the decision point. Defaults to 0.
        first_valid_trade_time (datetime.datetime): The timestamp of the first valid trade 
            associated with this decision point. Defaults to the current datetime.
        trade_direction (Literal["Bullish", "Bearish", "Undefined"]): The direction of the trade 
            associated with this decision point. Defaults to "Undefined".
            - "Bullish": Indicates an upward trade direction.
            - "Bearish": Indicates a downward trade direction.
            - "Undefined": Indicates no specific trade direction.
    Methods:
        __init__(self, High, Low, type="FTC", weight=0, first_valid_trade_time=datetime.datetime.now(), trade_direction="Undefined"):
            Initializes the DP_Parameteres_Class object with the provided attributes.
        ID_generator_Function(self):
            Generates a unique identifier (ID) for the decision point based on the 
            timestamps of the High and Low flag points. If either High or Low is None 
            or their timestamps are unavailable, the ID is set to None.
        __repr__(self):
            Returns a string representation of the DP_Parameteres_Class object, 
            including its type, High, Low, weight, first_valid_trade_time, and trade_direction.
    """
    
    def __init__(self, 
                High: FlagPoint_Class, 
                Low: FlagPoint_Class,
                type: typing.Literal["FTC", "EL", "MPL"] = "FTC",
                weight: int = 0,
                first_valid_trade_time : datetime.datetime = datetime.datetime.now(),
                trade_direction : typing.Literal["Bullish", "Bearish", "Undefined"] = "Undefined"):
        """DP_Parameteres_Class is a class designed to encapsulate the parameters and attributes 
        associated with a trading bot's decision point (DP). It includes information about 
        high and low flag points, trade type, weight, first valid trade time, and trade direction.
        Attributes:
            High (FlagPoint_Class): The high flag point object, which contains information 
                about the high point in a trade decision.
            Low (FlagPoint_Class): The low flag point object, which contains information 
                about the low point in a trade decision.
            type (Literal["FTC", "EL", "MPL"]): The type of the decision point. Defaults to "FTC".
                - "FTC": First Trade Confirmation
                - "EL": Entry Level
                - "MPL": Mid-Point Level
            weight (int): The weight or significance of the decision point. Defaults to 0.
            first_valid_trade_time (datetime.datetime): The timestamp of the first valid trade 
                associated with this decision point. Defaults to the current datetime.
            trade_direction (Literal["Bullish", "Bearish", "Undefined"]): The direction of the trade 
                associated with this decision point. Defaults to "Undefined".
                - "Bullish": Indicates an upward trade direction.
                - "Bearish": Indicates a downward trade direction.
                - "Undefined": Indicates no specific trade direction.
        """
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
        if self.High is not None and self.Low is not None and self.High.time is not None and self.Low.time is not None:
            self.id = f"H {self.High.time} & L {self.Low.time}"
        else:
            self.id = None
        return self.id
    
    def __repr__(self):
        return (f"DP_Parameteres_Class(type={self.type}, High={self.High}, Low={self.Low}, "
                f"weight={self.weight}, first_valid_trade_time={self.first_valid_trade_time}, "
                f"trade_direction={self.trade_direction})")