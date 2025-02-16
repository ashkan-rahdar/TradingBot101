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

from classes.Flag_Detector import FlagDetector
from classes.Flag import Flag
from functions.logger import logger
from functions.run_with_retries import run_with_retries
from functions.Figure_Flag import Figure_Flag
from functions.Reaction_detector import main_reaction_detector
from classes.Database import Database

class Timeframe:
    def __init__(self, timeframe: str):
        self.timeframe = timeframe
        global config
        self.MySQL_DataBase = Database(timeframe)
        self.detector = FlagDetector(timeframe, self.MySQL_DataBase)
    
    def set_data(self, DataSet: pd.DataFrame):
        self.DataSet = DataSet

    async def detect_flags(self):
        try:
            await run_with_retries(self.detector.run_detection,self.DataSet)
            # self.FLAGS = self.detector.flags
            # print(Fore.BLACK + Style.DIM + f"{self.timeframe} Flags: \n {self.FLAGS}" + Style.RESET_ALL)
        except RuntimeError as e:
            logger.error(f"{self.timeframe} Flag detection failed: {e}")
            # self.FLAGS = pd.DataFrame()

    # async def save_to_excel(self):
    #     file_name = f"{self.timeframe}_FLAGS.xlsx"
    #     sheet_name = "Flags Data"

    #     try:
    #         if not os.path.exists(file_name):
    #             with pd.ExcelWriter(file_name, engine="openpyxl", mode="w") as writer:
    #                 self.FLAGS.to_excel(writer, index=False, sheet_name=sheet_name)
    #         else:
    #             with pd.ExcelWriter(file_name, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    #                 self.FLAGS.to_excel(writer, index=False, sheet_name=sheet_name)
            
    #         print(f"Updated {file_name} at {pd.Timestamp.now()}")
    #     except Exception as e:
    #         print(f"Failed to save to Excel: {e}")

    async def save_to_DB(self):
        try:
            for _, flag in self.FLAGS.iterrows():
                print(type(flag))
                await self.MySQL_DataBase.save_data(flag)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"An error occurred in saving Data in DB: {e}" + Style.RESET_ALL)
            logger.critical(f"An error occurred in saving Data in DB: {e}")
    
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

CTimeFrames = [Timeframe(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]