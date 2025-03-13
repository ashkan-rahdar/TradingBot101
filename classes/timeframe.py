import sys
import os
from openpyxl import load_workbook
import pandas as pd
from colorama import Fore,Style
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

from classes.Flag_Detector import FlagDetector_Class
from classes.Flag import Flag_Class
from functions.logger import print_and_logging_Function
from functions.run_with_retries import run_with_retries_Function
from functions.Reaction_detector import main_reaction_detector
from classes.Database import Database_Class

class Timeframe_Class:
    def __init__(self, The_timeframe: str):
        self.timeframe = The_timeframe
        self.DataSet = pd.DataFrame()
        global config
        self.MySQL_DataBase = Database_Class(The_timeframe)
        self.detector = FlagDetector_Class(The_timeframe, self.MySQL_DataBase)
    
    def set_data_Function(self, aDataSet: pd.DataFrame):
        self.DataSet = aDataSet

    async def detect_flags_Function(self):
        try:
            await run_with_retries_Function(self.detector.run_detection_Function,self.DataSet)
        except RuntimeError as The_error:
            print_and_logging_Function("error", f"{self.timeframe} Flag detection failed: {The_error}", "title")
    
    async def development(self):
        try:
            await run_with_retries_Function(main_reaction_detector, self.DataSet)
        except RuntimeError as e:
            print_and_logging_Function("error", f"Reaction detection failed: {e}", "title")

    async def validate_DPs_Function(self):
        return

CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]