import sys
import os
import pandas as pd
import json
import asyncio
import bisect
import numpy as np
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

from classes.DP_Parameteres import DP_Parameteres_Class
from classes.Flag_Detector import FlagDetector_Class
from classes.Metatrader_Module import CMetatrader_Module
from functions.logger import print_and_logging_Function
from functions.run_with_retries import run_with_retries_Function
from functions.Reaction_detector import main_reaction_detector
from classes.Database import Database_Class

class Timeframe_Class:
    """
    Timeframe_Class is a class designed to handle operations related to timeframes in a trading bot. 
    It integrates with a MySQL database, performs flag detection, validates decision points (DPs), 
    and manages trading positions.
    Attributes:
        timeframe (str): The timeframe associated with this instance.
        DataSet (pd.DataFrame): A DataFrame containing market data for the given timeframe.
        CMySQL_DataBase (Database_Class): An instance of the database class for interacting with MySQL.
        detector (FlagDetector_Class): An instance of the flag detector class for detecting flags in the data.
        dps_to_update (list[tuple[int, int]]): A list of decision points (DPs) that need to be updated.
        Tradeable_DPs (list[tuple[DP_Parameteres_Class, int]]): A list of tradeable decision points.
        inserting_BackTest_DB (list[tuple]): A list of backtest positions to be inserted into the database.
    Methods:
        __init__(The_timeframe: str):
            Initializes the Timeframe_Class instance with the given timeframe.
            Inputs:
                - The_timeframe (str): The timeframe to be associated with this instance.
            Outputs:
                - None
        set_data_Function(aDataSet: pd.DataFrame):
            Sets the DataSet attribute with the provided market data.
            Inputs:
                - aDataSet (pd.DataFrame): The market data to be set.
            Outputs:
                - None
        async detect_flags_Function():
            Detects flags in the dataset using the detector instance.
            Inputs:
                - None
            Outputs:
                - None
            Exceptions:
                - RuntimeError: If flag detection fails.
        async development():
            Runs the main reaction detector on the dataset.
            Inputs:
                - None
            Outputs:
                - None
            Exceptions:
                - RuntimeError: If reaction detection fails.
        async validate_DPs_Function():
            Validates decision points (DPs) and updates their weights in the database.
            Inputs:
                - None
            Outputs:
                - None
            Exceptions:
                - Exception: If any error occurs during validation or database operations.
        async Each_DP_validation_Function(aDP: DP_Parameteres_Class, The_index_DP: str):
            Validates a single decision point (DP) and determines its tradeability.
            Inputs:
                - aDP (DP_Parameteres_Class): The decision point to validate.
                - The_index_DP (str): The index of the decision point.
            Outputs:
                - None
            Exceptions:
                - Exception: If any error occurs during validation.
        async Update_Positions_Function():
            Opens new trading positions for tradeable decision points and inserts them into the database.
            Inputs:
                - None
            Outputs:
                - None
            Exceptions:
                - Exception: If any error occurs during position opening or database insertion.
    """
    
    def __init__(self, The_timeframe: str):
        """
        Initializes an instance of the class with the specified timeframe.
        Args:
            The_timeframe (str): A string representing the timeframe for the instance.
        Attributes:
            timeframe (str): Stores the provided timeframe.
            DataSet (pd.DataFrame): An empty pandas DataFrame initialized for storing data.
            CMySQL_DataBase (Database_Class): An instance of the `Database_Class` initialized with the given timeframe.
            detector (FlagDetector_Class): An instance of the `FlagDetector_Class` initialized with the given timeframe 
                                           and the `CMySQL_DataBase` instance.
        This constructor sets up the necessary attributes for the class, including initializing a database connection 
        and a flag detector specific to the provided timeframe.
        """
        
        self.timeframe = The_timeframe
        self.DataSet = pd.DataFrame()
        global config
        self.CMySQL_DataBase = Database_Class(The_timeframe)
        self.detector = FlagDetector_Class(The_timeframe, self.CMySQL_DataBase)
    
    def set_data_Function(self, aDataSet: pd.DataFrame):
        self.DataSet = aDataSet

    async def detect_flags_Function(self):
        """
        Asynchronously detects flags within a given dataset using a detection function.
        This function attempts to run a detection process on a dataset using the `run_with_retries_Function` 
        utility to handle retries in case of transient failures. If the detection process fails, it logs 
        the error and provides feedback about the failure.
        Inputs:
        - `self`: The instance of the class that contains this method. It provides access to the `detector`, 
          `DataSet`, and `timeframe` attributes.
            - `self.detector.run_detection_Function`: A callable function that performs the actual flag 
              detection logic.
            - `self.DataSet`: The dataset on which the flag detection is performed.
            - `self.timeframe`: A string representing the timeframe associated with the detection process.
        Outputs:
        - None: This function does not return any value. It performs its operations asynchronously and 
          handles errors by logging them.
        Exceptions:
        - Catches `RuntimeError` if the detection process fails and logs the error message using the 
          `print_and_logging_Function` utility.
        """
        
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
        """
        Asynchronous function to validate and process tradeable data points (DPs) for backtesting and database updates.
        This function performs the following tasks:
        1. Retrieves a list of tradeable DPs from the database.
        2. Prepares the dataset for processing by converting the 'time' column to a datetime format.
        3. Validates each DP asynchronously using `Each_DP_validation_Function`.
        4. Inserts validated backtest positions into the database.
        5. Updates the weights of DPs in the database if necessary.
        
        Attributes:
            self.dps_to_update (list[tuple[int, int]]): A list of tuples containing DP IDs and their updated weights.
            self.Tradeable_DPs (list[tuple[DP_Parameteres_Class, int]]): A list of tradeable DP objects and their indices.
            self.inserting_BackTest_DB (list[tuple[str, str, float, float, float, datetime.datetime, int, int, float]]): 
                A list of tuples representing backtest positions to be inserted into the database.
        Steps:
            1. Retrieve tradeable DPs using `self.CMySQL_DataBase._get_tradeable_DPs_Function()`.
            2. Convert the 'time' column in `self.DataSet` to datetime format for processing.
            3. Validate each DP asynchronously using `Each_DP_validation_Function` and gather results.
            4. Insert validated backtest positions into the database using `self.CMySQL_DataBase._insert_positions_batch()`.
            5. Update DP weights in the database using `self.CMySQL_DataBase._update_dp_weights_Function()` if there are updates.
        Exceptions:
            - Logs errors encountered during backtest position insertion or DP weight updates.
            - Logs any general errors encountered during the validation process.
        Returns:
            None
        """
        
        try:
            # Initialize list to store DPs that need to be updated
            self.dps_to_update : list[tuple[str, float]] = []
            self.Tradeable_DPs: list[tuple[DP_Parameteres_Class, int]] = []
            self.inserting_BackTest_DB: list[tuple[str, float]] = []
            
            valid_DPs = await self.CMySQL_DataBase._get_tradeable_DPs_Function()
            
            # Pre-calculate these values once
            self.DataSet['time'] = self.DataSet['time'].astype('datetime64[ns]')
            
            tasks = []
            for The_valid_DP, index_of_DP in valid_DPs:
                task = self.Each_DP_validation_Function(The_valid_DP, index_of_DP)
                tasks.append(task)
            
            await asyncio.gather(*tasks)  # Await all tasks
            
            try:
                await self.CMySQL_DataBase._update_dp_Results_Function(self.inserting_BackTest_DB)
                if len(self.inserting_BackTest_DB) > 0 :
                    print_and_logging_Function("info", f"{len(self.inserting_BackTest_DB)} backtest positions inserted in DB", "title")
            except Exception as e:
                print_and_logging_Function("error", f"Error in inserting BackTest position in DB: {e}", "title")
                
            # Batch update the database
            if self.dps_to_update:
                try:
                    await self.CMySQL_DataBase._update_dp_weights_Function(self.dps_to_update)
                except Exception as e:
                    raise e
                
        except Exception as e:
            print_and_logging_Function("error", f"Error in validating DPs: {e}", "title")
            
    async def Each_DP_validation_Function(self, aDP: DP_Parameteres_Class, The_index_DP: str):
        """
        Validates a Decision Point (DP) for trading based on the provided parameters and updates the relevant data structures.
        This function evaluates whether a given DP is valid for trading based on its trade direction (Bullish or Bearish),
        price levels, and the dataset of historical price data. It performs calculations to determine if the DP meets
        the conditions for a trade and updates internal lists for tradeable DPs, DPs to update, and backtesting results.
        Args:
            aDP (DP_Parameteres_Class): 
                An instance of the DP_Parameteres_Class containing the parameters of the Decision Point (DP) to validate.
                This includes attributes such as:
                    - `weight`: The weight of the DP (used to filter out invalid DPs).
                    - `first_valid_trade_time`: The earliest time the DP is valid for trading.
                    - `trade_direction`: The direction of the trade ("Bullish" or "Bearish").
                    - `Low.price`: The low price level of the DP.
                    - `High.price`: The high price level of the DP.
            The_index_DP (str): 
                A string identifier for the DP being validated.
        Returns:
            None: 
                The function does not return a value. Instead, it updates the following internal attributes of the class:
                    - `self.Tradeable_DPs`: A list of tuples containing tradeable DPs and their identifiers.
                    - `self.dps_to_update`: A list of tuples containing DPs that need to be updated and their identifiers.
                    - `self.inserting_BackTest_DB`: A list of tuples containing backtesting results for valid trades.
        Raises:
            Exception: 
                If an error occurs during validation, an exception is raised with a message indicating the DP and the error.
        Functionality:
            - Prepares the time, high, and low price series from the dataset for efficient processing.
            - Filters out invalid DPs based on their weight or if they are outside the valid time range.
            - For Bearish DPs:
                - Checks if any high price is greater than or equal to the DP's low price.
                - Calculates the maximum risk-reward ratio (RR) for the trade.
                - Updates the backtesting database or marks the DP as tradeable.
            - For Bullish DPs:
                - Checks if any low price is less than or equal to the DP's high price.
                - Calculates the maximum risk-reward ratio (RR) for the trade.
                - Updates the backtesting database or marks the DP as tradeable.
        """
        
        try:
            # Pre-calculate these values once outside the loop
            time_series = self.DataSet['time'].to_numpy(dtype='datetime64[ns]')
            high_series = self.DataSet['high'].values
            low_series = self.DataSet['low'].values
            
            if aDP is None or aDP.weight == 0:
                return
            
            index = bisect.bisect_right(time_series, np.datetime64(aDP.first_valid_trade_time))
            
            if index >= len(time_series):
                # raise Exception(f"No Valid Time entered in a {The_index_DP} DP")
                self.Tradeable_DPs.append((aDP, The_index_DP))
                return
            
            # Use NumPy's efficient array operations instead of loops
            if aDP.trade_direction == "Bearish":
                # Check if any high price is >= the DP's Low price
                open_hits = np.flatnonzero(high_series[index:] >= aDP.Low.price)
                if open_hits.size != 0:
                    entry_idx = index + open_hits[0]
                    lows = low_series[entry_idx:]
                    highs = high_series[entry_idx:]

                    sl_hits = np.flatnonzero(highs >= aDP.High.price)
                    sl_idx = entry_idx + sl_hits[0] if sl_hits.size > 0 else None
                    if sl_idx:
                        lows = low_series[entry_idx:sl_idx]
                        self.dps_to_update.append((The_index_DP, 0))
                       

                    if lows.size == 0:
                        max_rr = -1
                    else:
                        max_rr = (aDP.High.price - lows.min()) / (aDP.High.price - aDP.Low.price)

                    self.inserting_BackTest_DB.append((
                        The_index_DP,
                        max_rr
                    ))
                else:
                    self.Tradeable_DPs.append((aDP, The_index_DP))
                    
            elif aDP.trade_direction == "Bullish":
                # Check if any low price is <= the DP's High price
                open_hits = np.flatnonzero(low_series[index:] <= aDP.High.price)
                if open_hits.size != 0:
                    entry_idx = index + open_hits[0]
                    lows = low_series[entry_idx:]
                    highs = high_series[entry_idx:]
                    
                    sl_hits = np.flatnonzero(lows <= aDP.Low.price)
                    sl_idx = entry_idx + sl_hits[0] if sl_hits.size > 0 else None
                    if sl_idx:
                        highs = high_series[entry_idx:sl_idx]
                        self.dps_to_update.append((The_index_DP, 0))
                    
                    if highs.size == 0:
                        max_rr = -1
                    else:
                        max_rr = (highs.max() - aDP.High.price) / (aDP.High.price - aDP.Low.price)

                    self.inserting_BackTest_DB.append((
                        The_index_DP,
                        max_rr
                    ))
                else:
                    self.Tradeable_DPs.append((aDP, The_index_DP))

        except Exception as e:
            raise Exception(f"validating the {The_index_DP} DP: {e}")
    
    async def Update_Positions_Function(self):
        """
        This asynchronous function is responsible for updating trading positions by opening new positions 
        for tradeable decision points (DPs) that have not yet been traded. It interacts with a trading 
        module to open positions and inserts the details of successfully opened positions into a database.
        
        Inputs:
        - None (The function operates on the instance variables of the class it belongs to).
        
        Key Operations:
        1. Iterates through `self.Tradeable_DPs`:
            - For each tradeable decision point (DP) and its index, checks if the DP has already been traded 
              by verifying its presence in `self.CMySQL_DataBase.Traded_DP_Set`.
            - If the DP has not been traded:
                - Calls `CMetatrader_Module.Open_position_Function` to open a new position with the following parameters:
                    - `order_type`: Determines whether the order is "Buy Limit" or "Sell Limit" based on the trade direction.
                    - `vol`: Sets the volume of the trade (fixed at 0.01 in this implementation).
                    - `price`: Sets the entry price based on the trade direction.
                    - `sl`: Sets the stop-loss price based on the trade direction.
                    - `tp`: Sets the take-profit price based on the trade direction.
                - If the position opening fails, logs an error message.
                - If the position opening succeeds:
                    - Retrieves the correct order type using `CMetatrader_Module.reverse_order_type_mapping`.
                    - Appends the position details to the `inserting_positions_DB` list for later database insertion.
                    - Increments the `new_opened_positions` counter.
                    - Logs a success message for the newly opened position.
        2. Inserts the new positions into the database:
            - Calls `self.CMySQL_DataBase._insert_positions_batch` with the `inserting_positions_DB` list.
            - Logs the number of successfully opened and inserted positions.
            - Catches and logs any exceptions that occur during the database insertion process.
            
        Outputs:
        - None (The function performs operations and logs results but does not return any value).
        
        Notes:
        - The function relies on external modules (`CMetatrader_Module` and `self.CMySQL_DataBase`) for trading 
          and database operations, respectively.
        - The function uses `print_and_logging_Function` for logging messages of different severity levels 
          (e.g., "info", "error").
        - The function assumes that `self.Tradeable_DPs` is a list of tuples containing tradeable decision points 
          and their indices.
        """
        
        new_opened_positions = 0
        inserting_positions_DB: list[tuple[str, str, float, float, float, datetime.datetime, int, int, float]] = []

        for aDP, The_index in self.Tradeable_DPs:
            if The_index not in self.CMySQL_DataBase.Traded_DP_Set:
                result = CMetatrader_Module.Open_position_Function(
                    order_type="Buy Limit" if aDP.trade_direction == "Bullish" else "Sell Limit",
                    vol=0.01,
                    price=aDP.High.price if aDP.trade_direction == "Bullish" else aDP.Low.price,
                    sl=aDP.Low.price if aDP.trade_direction == "Bullish" else aDP.High.price,
                    tp=aDP.High.price + 2 * (aDP.High.price - aDP.Low.price) if aDP.trade_direction == "Bullish" else aDP.Low.price - 2 * (aDP.High.price - aDP.Low.price),
                )
                if result.retcode != CMetatrader_Module.mt.TRADE_RETCODE_DONE:
                    print_and_logging_Function("error", f"Error in opening position of DP No.{The_index}. The message \n {result}", "title")
                else:
                    if not config["runtime"]["Able_to_Open_positions"]:
                        CMetatrader_Module.cancel_order(result.order)
                    # Get the correct order type from the mapping
                    order_type = CMetatrader_Module.reverse_order_type_mapping.get(result.request.type)

                    inserting_positions_DB.append((
                        The_index,                # traded_dp_id
                        order_type,               # order_type
                        result.request.price,     # price
                        result.request.sl,        # sl
                        result.request.tp,        # tp
                        datetime.datetime.now(),  # Last_modified_time
                        result.request.volume,    # vol
                        result.order,             # order_id
                        0                         # The result of trade
                    ))

                    new_opened_positions += 1
                    print_and_logging_Function("info", f"New position opened: DP {The_index}", "description")
                    self.CMySQL_DataBase.Traded_DP_Set.add(The_index)
                     
        try:
            await self.CMySQL_DataBase._insert_positions_batch(inserting_positions_DB)
            if new_opened_positions:
                print_and_logging_Function("info", f"{new_opened_positions} New positions opened and inserted in DB", "title")
        except Exception as e:
            print_and_logging_Function("error", f"Error in inserting position in DB: {e}", "title")

CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]