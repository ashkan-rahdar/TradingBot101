import pandas

class FlagPoint_Class:
    """
    FlagPoint_Class is a class that represents a flag point in a trading bot system. 
    It encapsulates information about a specific point in time, including its price, timestamp, and an optional index.
    Attributes:
        price (int): The price value associated with the flag point.
        time (pandas.Timestamp): The timestamp indicating when the flag point occurred.
        index (int): An optional index value for the flag point. Defaults to -1.
        id (str): A unique identifier for the flag point, generated based on the price and time.
    Methods:
        __init__(price: int, time: pandas.Timestamp, index: int = -1):
            Initializes a new instance of the FlagPoint_Class with the given price, time, and optional index.
            Automatically calls the ID_generator_Function to generate a unique identifier for the instance.
            Args:
                price (int): The price value associated with the flag point.
                time (pandas.Timestamp): The timestamp indicating when the flag point occurred.
                index (int, optional): An optional index value for the flag point. Defaults to -1.
        ID_generator_Function():
            Generates a unique identifier (id) for the flag point based on its price and time attributes.
            If either price or time is None, the id is set to None.
            Returns:
                str: The generated unique identifier for the flag point, or None if price or time is missing.
    """
    
    def __init__(self, price: int, time: pandas.Timestamp, index: int = -1):
        """FlagPoint_Class is a class that represents a flag point in a trading bot system. 
        It encapsulates information about a specific point in time, including its price, timestamp, and an optional index.
        Attributes:
            price (int): The price value associated with the flag point assigned to self.price.
            time (pandas.Timestamp): The timestamp indicating when the flag point occurred.
            index (int): An optional index value for the flag point. Defaults to -1.
            id (str): A unique identifier for the flag point, generated based on the price and time.
        """
        self.price = price
        self.time = time
        self.index = index
        self.ID_generator_Function()
    def ID_generator_Function(self):
        if self.price is not None and self.time is not None:
            self.id = f"{self.price} in {self.time}"
        else:
            self.id = None
        return self.id