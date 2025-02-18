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
from functions.logger import The_logger
from functions.run_with_retries import run_with_retries_Function
from functions.Figure_Flag import Figure_Flag
from functions.Reaction_detector import main_reaction_detector
from classes.Database import Database_Class

class Timeframe_Class:
    def __init__(self, The_timeframe: str):
        self.timeframe = The_timeframe
        global config
        self.MySQL_DataBase = Database_Class(The_timeframe)
        self.detector = FlagDetector_Class(The_timeframe, self.MySQL_DataBase)
    
    def set_data_Function(self, aDataSet: pd.DataFrame):
        self.DataSet = aDataSet

    async def detect_flags_Function(self):
        try:
            await run_with_retries_Function(self.detector.run_detection_Function,self.DataSet)
        except RuntimeError as The_error:
            The_logger.error(f"{self.timeframe} Flag detection failed: {The_error}")
    
    # async def development(self, account_info):
    #     if config["runtime"]["development"]["status"]:
    #         # Step 3: Visualize Flags
    #         try:
    #             if config["runtime"]["development"]["visualazation"]["status_flags"]:
    #                 Figure_Flag(self.DataSet, self.FLAGS, self.timeframe)
    #         except Exception as e:
    #             logger.error(f"Visualization failed: {e}")
    #             print(Fore.RED + Style.BRIGHT + f"Visualization failed: {e}" + Style.RESET_ALL)


    #         # Step 4: React to Flags
    #         try:
    #             await run_with_retries(main_reaction_detector, self.FLAGS, self.DataSet, account_info.balance, self.timeframe)
    #             await self.save_to_excel()
    #         except RuntimeError as e:
    #             logger.error(f"Reaction detection failed: {e}")
    #             print(Fore.RED + Style.BRIGHT + f"Reaction detection failed: {e}" + Style.RESET_ALL)
    #             # Emergency fallback action, e.g., reset trades

CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]