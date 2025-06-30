import sys
import os
import pandas as pd
import json
import asyncio
import bisect
import numpy as np
import datetime
import random
import typing
import pickle
from sklearn.model_selection import train_test_split
from catboost import CatBoostClassifier, Pool

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

from classes.DP_Parameteres import DP_Parameteres_Class
from classes.Flag_Detector import FlagDetector_Class
from classes.Metatrader_Module import CMetatrader_Module
from functions.logger import print_and_logging_Function
from functions.run_with_retries import run_with_retries_Function
from classes.Database import Database_Class
from classes.Telegrambot import CTelegramBot
from classes.Position_Manager import Position_Manager_Class

TARGET_PROB: float = config["trading_configs"]["risk_management"]["MIN_Prob"]
Max_No_Trade_Daily: int = config["trading_configs"]["risk_management"]["Max_No_Trade_Daily"]
RETRAIN_EVERY: int = config["trading_configs"]["ML_Engine"]["Retrain_Every"]
MIN_Test_Dataset_size: int = config["trading_configs"]["ML_Engine"]["Min_Test_Dataset_size"]

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
        self.RANDOM_STATE = 42
    
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
            self.Tradeable_DPs: list[str] = []
            self.inserting_BackTest_DB: list[tuple[str, float]] = []
            
            valid_DPs = await self.CMySQL_DataBase._get_update_DPlist_Function()
            
            # Pre-calculate these values once
            self.DataSet['time'] = self.DataSet['time'].astype('datetime64[ns]')
            
            tasks = []
            for The_valid_DP, index_of_DP in valid_DPs:
                task = self.Each_DP_validation_Function(The_valid_DP, index_of_DP)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions= True)  # Await all tasks
            
            try:
                await self.CMySQL_DataBase._update_dp_Results_Function(self.inserting_BackTest_DB)
                if len(self.inserting_BackTest_DB) > 0 :
                    print_and_logging_Function("info", f"{len(self.inserting_BackTest_DB)} backtest positions inserted in DB", "description")
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
            high_series = self.DataSet['high'].to_numpy(dtype=float)
            low_series = self.DataSet['low'].to_numpy(dtype=float)
            
            if aDP is None or aDP.weight == 0:
                return
            
            index = bisect.bisect_right(time_series, np.datetime64(aDP.first_valid_trade_time))
            
            if index >= len(time_series):
                # raise Exception(f"No Valid Time entered in a {The_index_DP} DP")
                self.Tradeable_DPs.append(The_index_DP)
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
                    self.Tradeable_DPs.append(The_index_DP)
                    
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
                    self.Tradeable_DPs.append(The_index_DP)

        except Exception as e:
            raise Exception(f"validating the {The_index_DP} DP: {e}")
    
    async def ML_Main_Function(self):
        RR_levels = np.arange(1.25, 5.1, 0.25)  # Range of test RRs
        probs = []
        self.Do_Trade_DpList : list[tuple[DP_Parameteres_Class, typing.Union[str, None], float, float, float]] = []
        X_FTC, Y_FTC = await self.CMySQL_DataBase.Read_ML_table_Function()
        FTC_models, model_weights = self.RR_ML_Training(RR_levels, X_FTC, Y_FTC, "FTC")
        DP_TradeList = await self.CMySQL_DataBase._get_tradeable_DPs_Function(self.Tradeable_DPs)
        
        if any(np.isnan(k) for k in FTC_models.keys()):
            return
        
        for i in range(len(DP_TradeList)):
            The_DP = DP_TradeList[i]
            if(The_DP.type != "FTC"): 
                continue

            probs = np.array([
                    FTC_models[rr].predict_proba(The_DP.to_model_input_Function())[0, 1] for rr in RR_levels
                ])

            # Enforce monotonicity (with a threshold)
            if not np.all(probs[:-1] + 0.1 >= probs[1:]):
                continue

            reliable_idx = [i for i, p in enumerate(probs) if p*model_weights[RR_levels[i]] >= TARGET_PROB]
            if not reliable_idx:
                continue

            best_rr_idx = reliable_idx[-1]
            
            if all(probs[i] >= TARGET_PROB * 0.8 for i in range(best_rr_idx + 1)):
                best_rr : float = RR_levels[best_rr_idx]
                trade_risk_percent: float = 100 * Position_Manager_Class.Risk_Calculator_Function(Estimated_Trade_win_Prob= min(1,probs[best_rr_idx]*model_weights[RR_levels[best_rr_idx]]),
                                                                                    Estimated_trade_nums_Daily= Max_No_Trade_Daily,
                                                                                    Trade_RR= best_rr)
                
                self.Do_Trade_DpList.append((The_DP, The_DP.ID_generator_Function(), trade_risk_percent, best_rr, probs[best_rr_idx]*model_weights[RR_levels[best_rr_idx]]))

    def RR_ML_Training(self, RR_values: np.ndarray, Input: pd.DataFrame, Output: pd.DataFrame, DP_type: str = "FTC") -> tuple[dict[float, CatBoostClassifier], dict[float, float]]:
        try:
            # --- Load Counter ---
            self.retrain_counters = getattr(self, 'retrain_counters', {})
            self.retrain_counters[DP_type] = self.retrain_counters.get(DP_type, 0) + 1

            model_cache_path = f"{DP_type}_{self.timeframe}_models.pkl"

            # --- Use Cached Models if Available and Not Due for Retrain ---
            if os.path.exists(model_cache_path) and self.retrain_counters[DP_type] < RETRAIN_EVERY:
                with open(model_cache_path, "rb") as f:
                    models, model_weights = pickle.load(f)
                print_and_logging_Function("info", f"ML Engine {self.timeframe}: Using cached model for DP type '{DP_type}'. Retraining in {RETRAIN_EVERY - self.retrain_counters[DP_type]} iterations.","title")
                return models, model_weights

            # --- Otherwise, Retrain and Overwrite Cache ---
            self.retrain_counters[DP_type] = 0  # Reset counter
            
            # Start new modeling
            X_train, X_test, y_train, y_test = train_test_split(Input, Output, test_size=0.2, random_state = self.RANDOM_STATE)
            X_train = pd.DataFrame(X_train)
            X_test = pd.DataFrame(X_test)
            y_train = pd.DataFrame(y_train)
            y_test = pd.DataFrame(y_test)
            
            categorical_features = ["Is_related_DP_used", "Is_golfed", "Is_used_half"]
            
            models: dict[float, CatBoostClassifier] = {}
            model_weights : dict[float, float] = {}

            if y_test.shape[0] <= MIN_Test_Dataset_size:
                print_and_logging_Function("warning",f"Testing Dataset is under valid size: {MIN_Test_Dataset_size}. Using Total Dataset for weighting models...", "title")
                y_test = Output
                X_test = Input
            
            for rr in RR_values:
                try:
                    print_and_logging_Function("info", f"Training the {rr} model for {DP_type} {self.timeframe}", "title")
                    # Binary label for this RR
                    y_train_bin : pd.DataFrame = (y_train >= rr).astype(int)
                    y_test_bin : pd.DataFrame = (y_test >= rr).astype(int)
                    
                    # Create CatBoost Pools
                    train_pool = Pool(data= X_train, label=y_train_bin, cat_features=categorical_features)
                    
                    model = CatBoostClassifier(
                        iterations=1000,
                        learning_rate=0.01,
                        depth=6,
                        loss_function='Logloss',
                        eval_metric='AUC',
                        l2_leaf_reg=5,
                        bootstrap_type='Bayesian',
                        random_strength=5,
                        boosting_type='Ordered',
                        early_stopping_rounds=50,
                        auto_class_weights='Balanced',
                        verbose=False,
                        allow_writing_files=False
                    )
                    model.fit(train_pool)
                    models[rr] = model
                    
                    # Custom Metric For Testing the model                
                    test_pool = Pool(data= X_test, label= y_test_bin, cat_features=categorical_features)
                    Y_Testing_Prob = model.predict_proba(test_pool)[:, 1]
                    df = pd.DataFrame({
                        "predicted_prob": Y_Testing_Prob,
                        "actual": y_test_bin
                    })
                        
                    df["bucket"] = np.where(df["predicted_prob"] >= TARGET_PROB, "high", "low")

                    # Check if any high-probability samples exist
                    if (df["bucket"] == "high").sum() == 0:
                        print_and_logging_Function("warning",f"RR {rr} Timeframe {self.timeframe} -> \n No predictions with prob >= {TARGET_PROB}. \n Model is too conservative or threshold too high.Won't be considered as a valid model","title")
                        model_weights[rr] = 0.0
                        continue

                    # Group and calculate metrics
                    bucket_summary = df.groupby("bucket").agg({
                        "predicted_prob": "mean",
                        "actual": "mean"
                    }).rename(columns={"actual": "empirical_winrate"})

                    # Check high-prob group
                    high = bucket_summary.loc["high"]
                    if high["empirical_winrate"].item() < high["predicted_prob"].item() - 0.2:
                        print_and_logging_Function("warning",f"RR {rr} Timeframe {self.timeframe} -> \n High-prob group underperforms: empirical winrate {high['empirical_winrate']:.2f} is more than 0.2 less than predicted {high['predicted_prob']:.2f}.\n Won't be considered as a valid model", "title")
                        model_weights[rr] = 0.0
                        continue

                    # Check low-prob group if exists
                    if "low" in bucket_summary.index:
                        low = bucket_summary.loc["low"]
                        if low["empirical_winrate"].item() > 0.5:
                            print_and_logging_Function("warning",f"RR {rr} Timeframe {self.timeframe} -> \n Low-prob group too strong: empirical winrate is {low['empirical_winrate']:.2f} (> 0.5), check model discrimination. \n Won't be considered as a valid model", "title")
                            model_weights[rr] = 0.0
                            continue
                    model_weights[rr] = (high["empirical_winrate"].item() / high["predicted_prob"].item())
                except Exception as e:
                    raise Exception(f"Error-> ML engine -> training the ML model -> RR {rr} : {e}")
                        
            # Backtest filtering logic on test dataset
            result_on_test = 0
            succeeded_trades = 0
            total_trades = 0

            for i in range(len(X_test)):
                probs = []
                for rr in RR_values:
                    probs.append(models[rr].predict_proba(X_test.iloc[[i]])[0, 1])

                probs = np.array(probs)

                # Enforce monotonicity (with a threshold)
                if not np.all(probs[:-1] + 0.1 >= probs[1:]):
                    continue

                reliable_idx = [i for i, p in enumerate(probs) if p*model_weights[RR_values[i]] >= TARGET_PROB]
                if not reliable_idx:
                    continue

                best_rr_idx = reliable_idx[-1]
                if all(probs[i] >= TARGET_PROB * 0.8 for i in range(best_rr_idx + 1)):
                    best_rr : float = RR_values[best_rr_idx]
                    if all(probs[i] >= TARGET_PROB for i in range(best_rr_idx + 1)):
                        if y_test.iloc[i].item() >= best_rr:
                            result_on_test += Position_Manager_Class.Risk_Calculator_Function(Estimated_Trade_win_Prob= min(1,probs[best_rr_idx]*model_weights[RR_values[best_rr_idx]]),
                                                                                        Estimated_trade_nums_Daily= Max_No_Trade_Daily,
                                                                                        Trade_RR= best_rr) * best_rr
                            succeeded_trades += 1
                        else:
                            result_on_test -= Position_Manager_Class.Risk_Calculator_Function(Estimated_Trade_win_Prob= min(1,probs[best_rr_idx]*model_weights[RR_values[best_rr_idx]]),
                                                                                        Estimated_trade_nums_Daily= Max_No_Trade_Daily,
                                                                                        Trade_RR= best_rr)
                        total_trades += 1
            winrate = succeeded_trades / total_trades if total_trades > 0 else 0
            print_and_logging_Function("info", f"The result of BackTest on test dataset: \n {result_on_test * 100} percent profit with the {winrate} winrate in {total_trades} trades", "title")
            if winrate <= (TARGET_PROB**2) and result_on_test <= 0 :
                models = {float("nan"): CatBoostClassifier()} 
                self.RANDOM_STATE = random.randint(10, 50)
                print_and_logging_Function("warning", "Based on current data Bot is not profitable", "title")
                
            # Save updated models and weights
            with open(model_cache_path, "wb") as f:
                pickle.dump((models, model_weights), f)
            return models, model_weights
        except Exception as e:
            print_and_logging_Function("error", f"An error occured in Backtesting the ML on Test Dataset:{e}", "title")
            return {float("nan"): CatBoostClassifier()} , {}
    
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
        inserting_positions_DB: list[tuple[str, str, float, float, float, datetime.datetime, int, int, int, float]] = []

        for aDP, The_index, Estimated_Risk, Estimated_RR, probability in self.Do_Trade_DpList:
            # Trade new detected DPs
            if The_index not in self.CMySQL_DataBase.Traded_DP_Dict.keys():
                try:
                    if aDP.trade_direction == "Bullish":    
                        result = CMetatrader_Module.Open_position_Function(
                            order_type=     "Buy Limit",
                            vol=            Position_Manager_Class.Vol_Calculator_RiskBased_Function(aDP.High.price, aDP.Low.price, Estimated_Risk, config["trading_configs"]["asset"]),
                            price=          aDP.High.price,
                            sl=             aDP.Low.price,
                            tp=             aDP.High.price + Estimated_RR * (aDP.High.price - aDP.Low.price),
                            comment =       f"{int(probability * 100)}% chance, {self.timeframe}",
                            
                        )
                    else:
                        result = CMetatrader_Module.Open_position_Function(
                            order_type=     "Sell Limit",
                            vol=            Position_Manager_Class.Vol_Calculator_RiskBased_Function(aDP.High.price, aDP.Low.price, Estimated_Risk, config["trading_configs"]["asset"]),
                            price=          aDP.Low.price,
                            sl=             aDP.High.price,
                            tp=             aDP.Low.price - Estimated_RR * (aDP.High.price - aDP.Low.price),
                            comment =       f"{int(probability * 100)}% chance, {self.timeframe}",
                        )
                    if result is None:
                        continue
                    # Not a valid trade (Not MT5 error!)
                    # ========================================================
                    # ========================================================
                    # ========================================================
                    
                    elif result.retcode != CMetatrader_Module.mt.TRADE_RETCODE_DONE: # type: ignore
                        print_and_logging_Function("error", f"Error in opening position of DP No.{The_index}. The message \n {result}", "title")
                    else:
                        if not config["runtime"]["Able_to_Open_positions"]:
                            CMetatrader_Module.cancel_order(result.order) # type: ignore
                        # Get the correct order type from the mapping
                        order_type = CMetatrader_Module.reverse_order_type_mapping.get(result.request.type) # type: ignore

                        inserting_positions_DB.append((
                            The_index,                # traded_dp_id
                            order_type,               # order_type
                            result.request.price,     # price # type: ignore
                            result.request.sl,        # sl # type: ignore
                            result.request.tp,        # tp # type: ignore
                            datetime.datetime.now(),  # Last_modified_time
                            result.request.volume,    # vol # type: ignore
                            result.order,             # order_id # type: ignore
                            int(probability * 100),   # Estimated win chance
                            0                         # The result of trade
                        )) # type: ignore

                        new_opened_positions += 1
                        print_and_logging_Function("info", f"New position opened: DP {The_index}", "description")
                        self.CMySQL_DataBase.Traded_DP_Dict[The_index] = {"TP": result.request.tp, "Vol": result.request.volume, "Order_ID": result.order} # type: ignore
                        try:
                            CTelegramBot.notify_placed_position(order_type, result.request.price, result.request.sl, result.request.tp, result.request.volume, int(probability * 100), result.order) # type: ignore
                        except Exception as e:
                            print_and_logging_Function("error", f"{e}", "title")

                except RuntimeError as e:
                    print_and_logging_Function("error", f"Error in opening the position of DP No. {The_index}: {e}")
            # Modify Trades which their info has been changed
            else:
                try:
                    previous_info = self.CMySQL_DataBase.Traded_DP_Dict[The_index] # type: ignore
                    if aDP.trade_direction == "Bullish":    
                        new_TP = aDP.High.price + Estimated_RR * (aDP.High.price - aDP.Low.price)
                    else:
                        new_TP = aDP.Low.price - Estimated_RR * (aDP.High.price - aDP.Low.price)
                        
                    # Looking for TP changes
                    if new_TP < previous_info["TP"]:
                        result = CMetatrader_Module.modify_pending_order_Function(self.CMySQL_DataBase.Traded_DP_Dict[The_index]["Order_ID"], new_TP) # type: ignore
                        if result is None:
                            continue
                            # An error happened (Not Mt5 error, should alert user later)
                            # ========================================================
                            # ========================================================
                            # ========================================================
                        elif result.retcode != CMetatrader_Module.mt.TRADE_RETCODE_DONE:
                            continue
                            # An error happened (Mt5 error, should alert user later)
                            # ========================================================
                            # ========================================================
                            # ========================================================
                        else:
                            CTelegramBot.send_message(
                                text=f"✏️ Take-Profit Updated\n\nOrder ID: {self.CMySQL_DataBase.Traded_DP_Dict[The_index]['Order_ID']}\nPrevious TP: {previous_info['TP']}\nNew TP: {result.request.tp}\n\nThis adjustment was made based on updated system logic."  # type: ignore
                            )

                    # Looking for vol changes 
                    # ========================================================
                    # ========================================================
                    # ========================================================
                    
                except Exception as e:
                    print_and_logging_Function("error", e, "title") # type: ignore
        
        # insert The new positions in DB
        try:
            await self.CMySQL_DataBase._insert_positions_batch(inserting_positions_DB)
            if new_opened_positions:
                print_and_logging_Function("info", f"{new_opened_positions} New positions opened and inserted in DB", "title")
        except Exception as e:
            print_and_logging_Function("error", f"Error in inserting position in DB: {e}", "title")
            
        # Cancel positions which are not valid anymore
        try:
            Pending_position_IDs = await self.CMySQL_DataBase.Read_Pending_Positions_Function()  # noqa: F841
            valid_trade_indices = {The_index for _, The_index, _, _,_ in self.Do_Trade_DpList}  # noqa: F841
            cancelled_positions_IDs : dict[str, int] = {}
            
            for The_index, order_ID in Pending_position_IDs.items():
                if The_index not in valid_trade_indices:
                    result = CMetatrader_Module.cancel_order(order_ID)
                    if result.retcode != CMetatrader_Module.mt.TRADE_RETCODE_DONE: # type: ignore
                        print_and_logging_Function("error", f"Error in canceling {order_ID} position: {result}", "title")
                    else:
                        print_and_logging_Function("info", f"Cancelled order {order_ID}. No more valid position", "description")
                        cancelled_positions_IDs[The_index] = order_ID
                        CTelegramBot.send_message(
                            text=f"🚫 Order Cancelled\n\nOrder ID: {order_ID}\nReason: The setup is no longer valid based on current market conditions.\n\nTrade opportunity has been dismissed to ensure risk protection."
                        )
                 
            
            await self.CMySQL_DataBase.remove_cancelled_positions_Function(cancelled_positions_IDs)
        except Exception as e:
            print_and_logging_Function("error", f"Error in canceling invalid positions: {e}", "title")    
      
    async def Closing_positions_Function(self):
        # Alert users in Telegram
        try:
            CTelegramBot.send_message(text="⚠️Attention: Closing Positions⚠️\n\nDue to system conditions, please close all Pending positions immediately to avoid potential risk. Please wait for further notice.")
        except Exception as e:
            print_and_logging_Function("error", f"Error in sending message to Telegram for canceling positions...: {e}")
        
        # Cancel pending positions and remove from DB and memory
        try:
            Pending_position_IDs = await self.CMySQL_DataBase.Read_Pending_Positions_Function()
            cancelled_positions_IDs : dict[str, int] = {}
            for DP_Index, order_ID in Pending_position_IDs.items():
                result = CMetatrader_Module.cancel_order(order_ID)
                if result.retcode != CMetatrader_Module.mt.TRADE_RETCODE_DONE: # type: ignore
                    print_and_logging_Function("error", f"Error in canceling {order_ID} position: {result}", "title")
                else:
                    print_and_logging_Function("info", f"Cancelled order {order_ID}", "description")
                    cancelled_positions_IDs[DP_Index] = order_ID
                    
            await self.CMySQL_DataBase.remove_cancelled_positions_Function(cancelled_positions_IDs)
        except Exception as e:
            print_and_logging_Function("error", f"Error in canceling positions: {e}")
    
    async def Result_Reporter_Function(self):
        try:
            await self.CMySQL_DataBase.correct_position_results_Function()
            Result_percent, Result = await self.CMySQL_DataBase.PNL_Calculator_Function()
            winrate = await self.CMySQL_DataBase.winrate_Calculator_Function()
            try:
                CTelegramBot.send_message(
                    text=(
                        f"📊 Performance Report - {self.timeframe} 📊\n\n"
                        f"Result: {Result} ({Result_percent}%)\n"
                        f"Win Rate: {winrate:.2%}\n\n"
                        f"📈 Stay informed and manage risk accordingly."
                    )
                )
            except Exception as e:
                print_and_logging_Function("error", f"Error in sending message to Telegram for canceling positions...: {e}")
        except Exception as e:
            raise Exception(f"Error in calculating / Notify user PNL: {e}")
               
CTimeFrames = [Timeframe_Class(atimeframe) for atimeframe in config["trading_configs"]["timeframes"]]