import pandas

class FlagPoint_Class:
    def __init__(self, price: int, time: pandas.Timestamp, index: int = -1):
        self.price = price
        self.time = time
        self.index = index
        self.ID_generator_Function()
    def ID_generator_Function(self):
        if self.price != None and self.time != None:
            self.id = f"{self.price} in {self.time}"
        else:
            self.id = None
        return self.id