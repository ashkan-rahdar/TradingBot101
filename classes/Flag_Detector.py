import pandas as pd
import numpy as np
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag_Class
from functions.logger import print_and_logging_Function
from classes.FlagPoint import FlagPoint_Class
from classes.Database import Database_Class    

class FlagDetector_Class:
    """
    FlagDetector_Class is responsible for detecting bullish and bearish flag patterns in financial market data. 
    It processes a given dataset to identify local extrema (highs and lows) and uses these extrema to detect 
    flag patterns. The detected flags are stored for further analysis or persistence in a database.
    Attributes:
        CDataBase (Database_Class): An instance of the database class used for storing detected flags.
        DB_name_flag_points_table (str): The name of the database table for storing flag points.
        DB_name_flags_table (str): The name of the database table for storing flags.
        TimeFrame (str): The timeframe of the dataset being analyzed.
        Detected_Flags (list[Flag_Class]): A list to store detected flag patterns.
    Methods:
        __init__(The_timeframe: str, The_DataBase: Database_Class):
            Initializes the class with the given timeframe and database instance.
        detect_local_extremes_Function(The_dataset: pd.DataFrame):
            Identifies local maxima and minima in the dataset and marks them in the dataset.
        detect_bullish_flags_Function(The_dataset: pd.DataFrame):
            Asynchronously detects bullish flag patterns in the dataset.
        Each_bullish_detection_Function(The_highs, The_lows, The_index, The_dataset, The_local_tasks):
            Processes a single local maximum to detect a bullish flag pattern.
        detect_bearish_flags_Function(The_dataset: pd.DataFrame):
            Asynchronously detects bearish flag patterns in the dataset.
        Each_bearish_detection_Function(The_highs, The_lows, The_index, The_dataset, The_local_tasks):
            Processes a single local minimum to detect a bearish flag pattern.
        run_detection_Function(The_dataset: pd.DataFrame):
            Orchestrates the detection process for both bullish and bearish flags, 
            and saves the detected flags to the database.
    Usage:
        This class is designed to be used in trading bots or financial analysis tools 
        to identify flag patterns in market data. It supports asynchronous operations 
        for efficient processing of large datasets.
    """
    
    def __init__(self, The_timeframe:str, The_DataBase: Database_Class):
        """
        Initializes the Flag_Detector class.
        Args:
            The_timeframe (str): The timeframe for which the flag detection is being performed.
            The_DataBase (Database_Class): An instance of the Database_Class to interact with the database.
        Attributes:
            CDataBase (Database_Class): Stores the provided database instance for database operations.
            DB_name_flag_points_table (str): The name of the database table for storing flag points, based on the timeframe.
            DB_name_flags_table (str): The name of the database table for storing flags, based on the timeframe.
            TimeFrame (str): The timeframe for which the flag detection is being performed.
        """
        
        self.CDataBase = The_DataBase
        self.DB_name_flag_points_table = f"Flag_Points_{The_timeframe}"
        self.DB_name_flags_table = f"Flags_{The_timeframe}"
        self.TimeFrame = The_timeframe

    def detect_local_extremes_Function(self, The_dataset: pd.DataFrame):
        """
        Detect local extremes (local maxima and minima) in a given dataset.
        This function identifies local maxima and minima in the 'high' and 'low' columns 
        of the provided pandas DataFrame. A local maximum is a value that is greater than 
        its immediate neighbors, and a local minimum is a value that is smaller than its 
        immediate neighbors.
        Args:
            The_dataset (pd.DataFrame): A pandas DataFrame containing at least two columns:
                - 'high': A column representing the high values of a dataset (e.g., stock prices).
                - 'low': A column representing the low values of a dataset (e.g., stock prices).
        Returns:
            None: The function modifies the input DataFrame in place by adding two new columns:
                - 'is_local_max': A boolean column where True indicates a local maximum in the 'high' column.
                - 'is_local_min': A boolean column where True indicates a local minimum in the 'low' column.
        """
        
        highs = The_dataset['high']
        lows = The_dataset['low']

        # Using NumPy for vectorized operations
        is_local_max = (highs > np.roll(highs, 1)) & (highs > np.roll(highs, -1))
        is_local_min = (lows < np.roll(lows, 1)) & (lows < np.roll(lows, -1))

        # Assign results back to the dataset
        The_dataset['is_local_max'] = is_local_max
        The_dataset['is_local_min'] = is_local_min

    async def detect_bullish_flags_Function(self, The_dataset: pd.DataFrame):
        """
        Asynchronously detects bullish flag patterns in a given dataset.
        This function identifies potential bullish flag patterns in financial data by analyzing
        local maxima and minima within the dataset. It creates asynchronous tasks to process
        each detected local maximum and gathers the results.
        Args:
            The_dataset (pd.DataFrame): 
                A pandas DataFrame containing the financial data. It must include the following columns:
                - 'high': The high prices of the dataset.
                - 'low': The low prices of the dataset.
                - 'is_local_max': A boolean column indicating whether a given row is a local maximum.
        Behavior:
            - Logs the start of the bullish flag detection process for the specified timeframe.
            - Extracts the 'high' and 'low' price columns from the dataset.
            - Identifies indices of local maxima using the 'is_local_max' column.
            - For each local maximum, creates an asynchronous task to process the detection using 
              the `Each_bullish_detection_Function`.
            - Gathers all asynchronous tasks to ensure they complete execution.
        Returns:
            None: 
                This function does not return any value. It performs its operations asynchronously
                and may log results or update internal states as part of its execution.
        """
        
        local_tasks = []
        print_and_logging_Function("info", f" Bullish Flag Detecting of {self.TimeFrame} started...", "description")
        highs = The_dataset['high']
        lows = The_dataset['low']

        local_max_indices = np.where(The_dataset['is_local_max'].to_numpy())[0]
        for anIndex in local_max_indices:
            local_tasks.append(asyncio.create_task(self.Each_bullish_detection_Function(highs,lows,anIndex,The_dataset, local_tasks)))

        await asyncio.gather(*local_tasks)

    async def Each_bullish_detection_Function(self, The_highs, The_lows, The_index, The_dataset, The_local_tasks):
        """
        Asynchronously detects bullish flag patterns in a given dataset.
        This function identifies bullish flag patterns in financial data by analyzing 
        the highs and lows of a dataset. It determines the start, end, and low points 
        of the flag, and appends the detected flag to the `Detected_Flags` list.
        Args:
            The_highs (list or np.ndarray): A list or array of high prices in the dataset.
            The_lows (list or np.ndarray): A list or array of low prices in the dataset.
            The_index (int): The current index in the dataset being analyzed.
            The_dataset (pd.DataFrame): The dataset containing financial data, including 
                                        a "time" column for timestamps.
            The_local_tasks (list): A list to store asynchronous tasks (currently unused 
                                    but prepared for database operations).
        Returns:
            None: The function does not return any value. Instead, it appends detected 
                  bullish flag patterns to the `Detected_Flags` list.
        Key Steps:
            1. Identifies the high point of the flag using the current index.
            2. Finds the end of the flag by locating the next high greater than the 
               current high.
            3. Ensures the flag has a minimum length of 15 indices; otherwise, exits.
            4. Determines the low point of the flag by finding the lowest low between 
               the current index and the end of the flag.
            5. Identifies the start of the flag by finding the first low lower than 
               the low point of the flag.
            6. Creates a `Flag_Class` object representing the detected flag and appends 
               it to the `Detected_Flags` list.
        """
        
        high_of_flag = The_highs[The_index]

        # Find end of flag
        end_of_flag_indices = np.where((The_highs[The_index + 1:] > high_of_flag))[0] if The_index+1 < len(The_lows) else np.array([])
        if end_of_flag_indices.size == 0:
            return
        end_of_flag_index = The_index + 1 + end_of_flag_indices[0]

        if end_of_flag_index - The_index <= 15:
            return

        # Find low of flag (lowest low between i and end_of_flag_index)
        low_of_flag = The_lows[The_index:end_of_flag_index + 1].min()
        low_of_flag_index = The_index + np.where(The_lows[The_index:end_of_flag_index + 1] == low_of_flag)[0][-1]

        # Find start of flag (first low lower than low_of_flag)
        start_of_flag_index = None
        for j in range(1, The_index):
            if The_highs[The_index-j] >= high_of_flag:
                break
            elif The_lows[The_index-j] < low_of_flag:
                start_of_flag_index = The_index-j
                break
        
        if start_of_flag_index is None:
            return
        
        # Append valid flag
        flag = Flag_Class(
            The_flag_type=("Bullish" if low_of_flag_index != The_index else "Undefined"),
            The_high=FlagPoint_Class(price= high_of_flag,index= The_index, time=The_dataset["time"][The_index]),
            The_low=FlagPoint_Class(price= low_of_flag, index= low_of_flag_index, time= The_dataset["time"][low_of_flag_index]),
            The_data_in_flag= The_dataset.iloc[start_of_flag_index:end_of_flag_index + 1],
            The_start_index= start_of_flag_index,
            The_end_index= end_of_flag_index,
            The_start_FTC= end_of_flag_index)
        
        # The_local_tasks.append(asyncio.create_task(self.CDataBase.add_flag_Function(flag,self.DB_name_flags_table)))
        self.Detected_Flags.append(flag)

    async def detect_bearish_flags_Function(self, The_dataset: pd.DataFrame):
        """
        Asynchronously detects bearish flag patterns in a given dataset.
        This function identifies potential bearish flag patterns in financial data by analyzing 
        local minima and performing further detection tasks for each identified local minimum.
        Args:
            The_dataset (pd.DataFrame): 
                A pandas DataFrame containing the financial data. It is expected to have the following columns:
                - 'high': The high prices of the dataset.
                - 'low': The low prices of the dataset.
                - 'is_local_min': A boolean column indicating whether a given row is a local minimum.
        Workflow:
            1. Logs the start of the bearish flag detection process for the specified timeframe.
            2. Extracts the 'high' and 'low' price columns from the dataset.
            3. Identifies the indices of rows where 'is_local_min' is True.
            4. For each identified local minimum index:
                - Creates an asynchronous task to perform detailed bearish flag detection using 
                  the `Each_bearish_detection_Function`.
            5. Waits for all detection tasks to complete using `asyncio.gather`.
        Returns:
            None: 
                This function does not return any value. It performs its operations asynchronously 
                and may log information or update internal states as part of its execution.
        """
        
        local_tasks = []
        print_and_logging_Function("info", f" Bearish Flag Detecting of {self.TimeFrame} started...", "description")
        highs = The_dataset['high']
        lows = The_dataset['low']

        local_min_indices = np.where(The_dataset['is_local_min'].to_numpy())[0]
        for anindex in local_min_indices:
            local_tasks.append(asyncio.create_task(self.Each_bearish_detection_Function(highs,lows,anindex, The_dataset, local_tasks)))

        await asyncio.gather(*local_tasks)

    async def Each_bearish_detection_Function(self, The_highs, The_lows, The_index, The_dataset, The_local_tasks):
        """
        Asynchronously detects bearish flag patterns in a given dataset.
        This function identifies bearish flag patterns in financial data by analyzing 
        highs and lows of price movements. It determines the start, high, low, and end 
        of a bearish flag and appends the detected flag to the `Detected_Flags` list.
        Args:
            The_highs (list or np.ndarray): A list or array of high prices in the dataset.
            The_lows (list or np.ndarray): A list or array of low prices in the dataset.
            The_index (int): The current index in the dataset being analyzed.
            The_dataset (pd.DataFrame): The dataset containing price data, including a "time" column.
            The_local_tasks (list): A list to store asynchronous tasks (currently unused in the function).
        Returns:
            None: The function does not return a value. Instead, it appends detected flags 
            to the `Detected_Flags` list as instances of the `Flag_Class`.
        Key Steps:
            1. Identify the low of the flag at the given index (`low_of_flag`).
            2. Find the end of the flag by locating the first low below `low_of_flag` after the current index.
            3. Ensure the flag has a minimum length of 15 indices; otherwise, return early.
            4. Determine the high of the flag (`high_of_flag`) as the highest high between the current index 
               and the end of the flag.
            5. Locate the start of the flag by finding the first high lower than `high_of_flag` before the current index.
            6. If a valid start of the flag is found, create a `Flag_Class` instance with the detected flag details.
            7. Append the detected flag to the `Detected_Flags` list.
        Note:
            - The function assumes the dataset contains a "time" column for timestamp information.
            - The `Flag_Class` and `FlagPoint_Class` are custom classes used to represent the flag and its points.
            - The `The_local_tasks` argument is included but not actively used in the current implementation.
        """
        
        low_of_flag = The_lows[The_index]

        # Find end of flag
        end_of_flag_indices = np.where((The_lows[The_index + 1:] < low_of_flag))[0] if The_index+1 < len(The_lows) else np.array([])
        if end_of_flag_indices.size == 0:
            return
        end_of_flag_index = The_index + 1 + end_of_flag_indices[0]

        if end_of_flag_index - The_index <= 15:
            return

        # Find high of flag (highest high between i and end_of_flag_index)
        high_of_flag = The_highs[The_index:end_of_flag_index + 1].max()
        high_of_flag_index = The_index + np.where(The_highs[The_index:end_of_flag_index + 1] == high_of_flag)[0][-1]

        # Find start of flag (first high lower than high_of_flag)
        start_of_flag_index = None
        for j in range(1, The_index):
            if The_lows[The_index-j] <= low_of_flag:
                break
            elif The_highs[The_index-j] > high_of_flag:
                start_of_flag_index = The_index-j
                break
        
        if start_of_flag_index is None:
            return
        
        # Append valid flag
        flag = Flag_Class(
            The_flag_type= ("Bearish" if high_of_flag_index != The_index else "Undefined"),
            The_high=FlagPoint_Class(price= high_of_flag, index= high_of_flag_index, time= The_dataset["time"][high_of_flag_index]),
            The_low=FlagPoint_Class(price= low_of_flag, index= The_index, time= The_dataset["time"][The_index]),
            The_data_in_flag= The_dataset.iloc[start_of_flag_index:end_of_flag_index + 1],
            The_start_index= start_of_flag_index,
            The_end_index= end_of_flag_index,
            The_start_FTC= end_of_flag_index
        )

        # The_local_tasks.append(asyncio.create_task(self.CDataBase.add_flag_Function(flag,self.DB_name_flags_table)))
        self.Detected_Flags.append(flag)
            
    async def run_detection_Function(self, The_dataset: pd.DataFrame):
        """
        Asynchronously runs the flag detection process on a given dataset.
        This function orchestrates the detection of bullish and bearish flags in the provided dataset,
        saves the detected flags to the database, and logs the results. It uses asynchronous tasks
        to perform the detection and saving operations concurrently.
        Args:
            The_dataset (pd.DataFrame): The dataset containing the financial data on which the flag 
                                        detection process will be performed.
        Attributes:
            self.CDataBase.detected_flags (int): Resets the count of detected flags to zero before starting the detection.
            self.Detected_Flags (list[Flag_Class]): Initializes an empty list to store detected flags.
        Steps:
            1. `self.detect_local_extremes_Function(The_dataset)`:
               Identifies local extremes (highs and lows) in the dataset, which are used as a basis for flag detection.
            2. `self.detect_bullish_flags_Function(The_dataset)`:
               Asynchronously detects bullish flags in the dataset and appends the results to `self.Detected_Flags`.
            3. `self.detect_bearish_flags_Function(The_dataset)`:
               Asynchronously detects bearish flags in the dataset and appends the results to `self.Detected_Flags`.
            4. `self.CDataBase.save_flags_Function(self.Detected_Flags)`:
               Asynchronously saves the detected flags to the database.
            5. `await asyncio.gather(*tasks)`:
               Executes all asynchronous tasks concurrently.
            6. Logs the completion of the detection process and the number of new flags detected.
        Logging:
            - Logs an informational message when the detection process is completed.
            - Logs the number of new flags detected.
            - Logs an error message if an exception occurs during the detection process.
        Raises:
            Exception: If any error occurs during the detection process, it is logged and re-raised.
        Returns:
            None
        """
        
        tasks = []
        try:
            self.CDataBase.detected_flags = 0
            self.Detected_Flags : list[Flag_Class] = []
            self.detect_local_extremes_Function(The_dataset)
            tasks.append(asyncio.create_task(self.detect_bullish_flags_Function(The_dataset)))
            tasks.append(asyncio.create_task(self.detect_bearish_flags_Function(The_dataset)))
            tasks.append(asyncio.create_task(self.CDataBase.save_flags_Function(self.Detected_Flags)))
            await asyncio.gather(*tasks)
            print_and_logging_Function("info", f"Flag Detection of {self.TimeFrame} completed", "title")
            print_and_logging_Function("info", f"{self.CDataBase.detected_flags} New Flags detected", "description")
        except Exception as e:
            print_and_logging_Function("error", f"An error occurred during detection: {e}", "title")
            raise