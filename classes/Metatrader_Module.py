import MetaTrader5
import pandas as pd
from datetime import datetime  # noqa: F401
import json
import sys
import os
import asyncio
import typing

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import print_and_logging_Function
import parameters

# Load JSON config file
with open("./config.json", "r") as file:
    config = json.load(file)

class Metatrader_Module_Class:
    """ This class provides a set of methods to interact with the MetaTrader5 trading platform. It includes functionalities for opening positions, partially closing positions, canceling orders, fetching market data, and managing MetaTrader5 initialization and login.
    Attributes:
        Positions (pd.DataFrame): A DataFrame to store position data.
        mt (MetaTrader5): The MetaTrader5 module for interacting with the trading platform.
        timeframe_mapping (dict): A mapping of timeframe strings to MetaTrader5 constants.
        order_type_mapping (dict): A mapping of order type strings to MetaTrader5 constants.
        reverse_order_type_mapping (dict): A reverse mapping of MetaTrader5 order type constants to strings.
    Methods:
        __init__():
            Initializes the class attributes and mappings.
        Open_position_Function(order_type, vol, price, sl, tp, ticker):
            Opens a trading position with the specified parameters.
            Inputs:
                - order_type (str): The type of order ("Buy", "Sell", "Buy Limit", "Sell Limit").
                - vol (float): The volume of the trade.
                - price (float): The price at which to execute the trade.
                - sl (float): The stop-loss price.
                - tp (float): The take-profit price.
                - ticker (str): The trading symbol (default is from the global config).
            Outputs:
                - Returns the result of the order_send request.
        partial_close(ticket, ratio):
            Inputs:
                - ticket (int): The position ticket (order ID).
                - ratio (float): The fraction of the position to close (0 to 1).
            Outputs:
                - Returns True if the partial close is successful, otherwise False.
        cancel_order(order_number):
            Cancels a pending order by its order number.
            Inputs:
                - order_number (int): The order number to cancel.
            Outputs:
                - Returns the result of the order_send request.
        initialize_mt5_Function():
            Asynchronously initializes the MetaTrader5 platform.
            Inputs:
                - None.
            Outputs:
                - Raises a RuntimeError if initialization fails.
        login_mt5_Function():
            Asynchronously logs into the MetaTrader5 platform using credentials from the global config.
            Inputs:
                - None.
            Outputs:
                - Raises a RuntimeError if login fails.
        fetch_data_Function(The_timeframe, The_Dataset):
            Asynchronously fetches market data for a specified timeframe.
            Inputs:
                - The_timeframe (str): The timeframe for the data (e.g., "M15").
                - The_Dataset (pd.DataFrame): An optional existing dataset to compare with.
            Outputs:
                - Returns a DataFrame containing the fetched market data.
        main_fetching_data_Function(atimeframe, aDataset):
            Asynchronously initializes, logs in, and fetches market data.
            Inputs:
                - atimeframe (str): The timeframe for the data (e.g., "M15").
                - aDataset (pd.DataFrame): An optional existing dataset to compare with.
            Outputs:
                - Returns a DataFrame containing the fetched market data.
    """
    def __init__(self):
        """
        Initializes the Metatrader_Module class.
        This constructor sets up the initial state of the class, including:
        - A global configuration variable `config`.
        - An empty DataFrame `Positions` to store trading positions.
        - A reference to the MetaTrader5 module (`mt`) for interacting with the MetaTrader 5 platform.
        - A mapping `timeframe_mapping` that translates string representations of timeframes (e.g., "M1", "H1") 
          to their corresponding MetaTrader5 constants.
        - A mapping `order_type_mapping` that translates string representations of order types 
          (e.g., "Buy", "Sell Limit") to their corresponding MetaTrader5 constants.
        - A reverse mapping `reverse_order_type_mapping` that maps MetaTrader5 order type constants 
          back to their string representations.
        Attributes:
            Positions (pd.DataFrame): A DataFrame to store trading positions.
            mt (module): A reference to the MetaTrader5 module for trading operations.
            timeframe_mapping (dict): A dictionary mapping string timeframes to MetaTrader5 constants.
            order_type_mapping (dict): A dictionary mapping string order types to MetaTrader5 constants.
            reverse_order_type_mapping (dict): A dictionary mapping MetaTrader5 order type constants 
                                               back to their string representations.
        Note:
            This constructor does not take any input parameters and does not return any value.
        """
        
        global config
        self.Positions = pd.DataFrame()
        self.mt = MetaTrader5
        self.timeframe_mapping = {
            "M1": self.mt.TIMEFRAME_M1,
            "M2": self.mt.TIMEFRAME_M2,
            "M3": self.mt.TIMEFRAME_M3,
            "M4": self.mt.TIMEFRAME_M4,
            "M5": self.mt.TIMEFRAME_M5,
            "M6": self.mt.TIMEFRAME_M6,
            "M10": self.mt.TIMEFRAME_M10,
            "M12": self.mt.TIMEFRAME_M12,
            "M15": self.mt.TIMEFRAME_M15,
            "M20": self.mt.TIMEFRAME_M20,
            "M30": self.mt.TIMEFRAME_M30,
            "H1": self.mt.TIMEFRAME_H1,
            "H2": self.mt.TIMEFRAME_H2,
            "H3": self.mt.TIMEFRAME_H3,
            "H4": self.mt.TIMEFRAME_H4,
            "H6": self.mt.TIMEFRAME_H6,
            "H8": self.mt.TIMEFRAME_H8,
            "H12": self.mt.TIMEFRAME_H12,
            "D1": self.mt.TIMEFRAME_D1,
            "W1": self.mt.TIMEFRAME_W1,
            "MN1": self.mt.TIMEFRAME_MN1,
        }

        self.order_type_mapping: dict[typing.Literal["Buy", "Sell", "Buy Limit", "Sell Limit"],int] = {
            "Buy": self.mt.ORDER_TYPE_SELL,
            "Sell": self.mt.ORDER_TYPE_SELL,
            "Buy Limit": self.mt.ORDER_TYPE_BUY_LIMIT,
            "Sell Limit": self.mt.ORDER_TYPE_SELL_LIMIT
        }
        self.reverse_order_type_mapping = {value: key for key, value in self.order_type_mapping.items()}

    def Open_position_Function(self, 
                            order_type: typing.Literal["Buy", "Sell", "Buy Limit", "Sell Limit"], 
                            vol: float, 
                            price: float, 
                            sl: float, 
                            tp: float, 
                            ticker: str = config["trading_configs"]["asset"],
                            comment: str = "My Code opened"):
        """
        Opens a trading position in MetaTrader with specified parameters.
        This function sends a trade request to the MetaTrader platform to open a position 
        (market or pending order) based on the provided parameters. It dynamically adjusts 
        the precision of price, stop loss (sl), and take profit (tp) values based on the 
        symbol's decimal places.
        Parameters:
            order_type (typing.Literal["Buy", "Sell", "Buy Limit", "Sell Limit"]): 
                The type of order to execute. Can be one of the following:
                - "Buy": Market order to buy.
                - "Sell": Market order to sell.
                - "Buy Limit": Pending order to buy at a lower price.
                - "Sell Limit": Pending order to sell at a higher price.
            vol (float): 
                The volume of the trade (lot size).
            price (float): 
                The price at which the order should be executed. For market orders, 
                this is the current market price. For pending orders, this is the 
                desired price level.
            sl (float): 
                The stop loss price. The trade will automatically close if the price 
                reaches this level to limit losses.
            tp (float): 
                The take profit price. The trade will automatically close if the price 
                reaches this level to secure profits.
            ticker (str, optional): 
                The symbol (asset) to trade. Defaults to the asset specified in the 
                configuration file (`config["trading_configs"]["asset"]`).
        Returns:
            tuple: 
                A tuple containing the result of the trade request:
                - The first element is the result of the `order_send` method, which 
                contains details about the trade execution.
                - The second element is `None` if the trade request fails (e.g., if 
                symbol information cannot be retrieved).
        """
        try:        
            order_type_INT = self.order_type_mapping.get(order_type, None)
            # Get number of decimal places for the asset dynamically
            symbol_info = self.mt.symbol_info(ticker) # type: ignore
            if symbol_info is None:
                print(f"Error: Could not retrieve symbol info for {ticker}")
                return None, None
            
            digits = symbol_info.digits
            
            tick_value = symbol_info.trade_tick_value
            commission_per_lot = config["account_info"]["commision"]
            total_commission = commission_per_lot * vol

            # Adjust SL for commission
            sl_adjusted = sl
            if order_type == "Buy" or order_type == "Buy Limit":
                sl_adjusted = sl - (total_commission / tick_value)
            elif order_type == "Sell" or order_type == "Sell Limit":
                sl_adjusted = sl + (total_commission / tick_value)# Number of decimal places for the symbol

            request = {
                "action": self.mt.TRADE_ACTION_DEAL if (order_type_INT is not None and order_type_INT < 2) else self.mt.TRADE_ACTION_PENDING,
                "symbol": ticker,
                "volume": vol,
                "type": order_type_INT,
                "price": round(price, digits),  # Dynamically rounding based on symbol
                "sl": round(sl_adjusted, digits),
                "tp": round(tp, digits),
                "deviation": 20,
                "magic": 101,
                "comment": comment,
                "type_time": self.mt.ORDER_TIME_GTC,
                "type_filling": self.mt.ORDER_FILLING_FOK
            }
            return self.mt.order_send(request) # type: ignore
        except Exception as e:
            raise Exception(f"an Error occured in Opening position with {comment}: {e}")

    def partial_close(self, ticket: int, ratio: float  = 1):
        """
        Partially closes an open trading position based on the specified ticket and ratio.
        This method allows you to close a portion of an open position by specifying a ratio of the total volume to close. 
        It validates the input parameters, retrieves the position details, calculates the volume to close, and sends a 
        close order to the trading platform.
        Args:
            ticket (int): The unique identifier (ticket) of the position to be partially closed.
            ratio (float, optional): The fraction of the position's volume to close. Must be between 0 and 1. 
                                     Defaults to 1 (fully close the position).
        Returns:
            bool: 
                - True if the partial close operation is successful.
                - False if the operation fails due to invalid input, no matching position, or an error during the close request.
        Raises:
            None
        Notes:
            - The method ensures that the ratio is within the valid range (0 < ratio <= 1).
            - It checks if the volume to close meets the minimum volume requirements of the trading platform.
            - The method prints error messages for invalid inputs or failed operations.
            - The `magic` field in the close request is set to a fixed value (123456) for identification purposes.
        """
        
        # Ensure ratio is within valid range
        if not (0 < ratio <= 1):
            print("Invalid ratio. It must be between 0 and 1.")
            return False

        # Get open positions
        positions = self.mt.positions_get() # type: ignore

        if positions is None:
            print("No open positions")
            return False

        # Find the position with the given ticket
        position = next((p for p in positions if p.ticket == ticket), None)
        
        if position is None:
            print(f"No position found with ticket {ticket}")
            return False

        # Calculate volume to close
        volume_to_close = position.volume * ratio

        # Ensure the volume to close is valid (mt might have minimum volume limits)
        if volume_to_close < self.mt.symbol_info(position.symbol).volume_min: # type: ignore
            print(f"Volume to close ({volume_to_close}) is less than the minimum allowed.")
            return False

        # Create a close request
        close_request = {
            "action": self.mt.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": volume_to_close,
            "price": position.price_current,
            "type": self.mt.ORDER_TYPE_SELL if position.type == self.mt.POSITION_TYPE_BUY else self.mt.ORDER_TYPE_BUY,
            "position": ticket,
            "magic": 123456,
            "comment": "Partial close",
        }

        # Send the close order
        result = self.mt.order_send(close_request) # type: ignore

        if result and result.retcode == self.mt.TRADE_RETCODE_DONE:
            print(f"Successfully closed {ratio*100:.1f}% of position {ticket}. Remaining volume: {position.volume - volume_to_close:.2f}")
            return True
        else:
            print(f"Failed to partially close position {ticket}. Error code: {result.retcode}")
            return False

    def cancel_order(self, order_number):
        """
        Cancels an existing order in the MetaTrader platform.
        This function sends a request to the MetaTrader platform to remove an order
        specified by its order number. It constructs a request dictionary with the
        necessary parameters and sends it using the `order_send` method of the MetaTrader
        instance.
        Args:
            order_number (int): The unique identifier of the order to be canceled.
        Returns:
            dict: A dictionary containing the result of the order cancellation request.
            The structure and content of this dictionary depend on the MetaTrader API's
            response format.
        Notes:
            - The `self.mt.TRADE_ACTION_REMOVE` is used to specify the action type for
              removing an order.
            - The `comment` field in the request is set to "Order Removed" to provide
              additional context for the action.
        """
        
        # Create the request
        request = {
            "action": self.mt.TRADE_ACTION_REMOVE,
            "order": order_number,
            "comment": "Order Removed"
        }
        # Send order to mt
        order_result = self.mt.order_send(request) # type: ignore
        return order_result
    
    async def initialize_mt5_Function(self):
        """
        Asynchronously initializes the MetaTrader5 trading platform.
        This function attempts to initialize the MetaTrader5 platform using the `initialize` method 
        from the `mt` object. If the initialization fails, it logs an error message and raises a 
        `RuntimeError` to indicate the failure.
        Inputs:
            None
        Outputs:
            None
        Raises:
            RuntimeError: If the MetaTrader5 platform fails to initialize.
        Notes:
            - The `mt.initialize()` method is expected to return a boolean indicating the success 
              or failure of the initialization.
            - The `print_and_logging_Function` is used to log an error message in case of failure.
        """
        
        if not self.mt.initialize(): # type: ignore
            print_and_logging_Function("error", "MetaTrader5 initialization failed", "title")
            raise RuntimeError("MetaTrader5 initialization failed")

    async def login_mt5_Function(self):
        """
        Asynchronous function to log in to MetaTrader5 using account credentials.
        This function attempts to log in to the MetaTrader5 platform using the 
        account credentials provided in the global `config` dictionary. If the 
        login fails, it logs an error message and raises a `RuntimeError`.
        Inputs:
            - None (Relies on the global `config` dictionary for account credentials).
        Outputs:
            - None (Performs login operation and raises an exception on failure).
        Raises:
            - RuntimeError: If the login to MetaTrader5 fails.
        Side Effects:
            - Calls `print_and_logging_Function` to log an error message if the login fails.
            - Raises an exception to indicate a critical failure in the login process.
        """
        
        global config
        if not self.mt.login(config["account_info"]["login"], config["account_info"]["password"], config["account_info"]["server"]): # type: ignore
            print_and_logging_Function("error", "MetaTrader5 login failed", "title")
            raise RuntimeError("MetaTrader5 login failed")

    async def fetch_data_Function(self, The_timeframe = "M15", The_Dataset: pd.DataFrame = pd.DataFrame()):
        """
        Asynchronously fetches market data for a specified timeframe and returns it as a pandas DataFrame.
        This function interacts with a MetaTrader instance to retrieve historical market data for a given asset
        and timeframe. It continuously checks for new data and returns the updated dataset when new candles are available.
        If an emergency flag is set, the function terminates and returns an empty DataFrame.
        Args:
            The_timeframe (str, optional): The timeframe for the market data to fetch. Defaults to "M15".
                                           The timeframe should match the keys in `self.timeframe_mapping`.
            The_Dataset (pd.DataFrame, optional): A pandas DataFrame containing previously fetched data. Defaults to an empty DataFrame.
        Returns:
            pd.DataFrame: A pandas DataFrame containing the fetched market data. If no new data is available or an error occurs,
                          an empty DataFrame is returned.
        Raises:
            RuntimeError: If an exception occurs during the data fetching process, a RuntimeError is raised with the error details.
        Notes:
            - The function uses `self.timeframe_mapping` to map the provided timeframe to the appropriate MetaTrader timeframe.
            - It checks the validity of the trading symbol and ensures the market is open before fetching data.
            - If `The_Dataset` is not empty, it waits for new candles to appear before returning the updated dataset.
            - The function respects an emergency flag (`parameters.The_emergency_flag`) to terminate its execution early.
            - Logs are generated for both successful and failed operations using `print_and_logging_Function`.
        Example:
            async def main():
                data = await fetch_data_Function(The_timeframe="H1")
                print(data)
        """
        
        selected_timeframe = self.timeframe_mapping.get(The_timeframe, None)
        try:
            symbol_info = self.mt.symbol_info(config["trading_configs"]["asset"]) # type: ignore
            if symbol_info is None or not symbol_info.trade_mode:
                print_and_logging_Function("error", "symbol is invalid or market is close now", "description")

            if len(The_Dataset) != 0:
                    print_and_logging_Function("info", f"Waiting for new {The_timeframe} candles...", "description")

            while not parameters.shutdown_flag:
                DataSet = pd.DataFrame(self.mt.copy_rates_from_pos(config["trading_configs"]["asset"],  # type: ignore
                                                            selected_timeframe, 
                                                            0, 
                                                            10000))
                DataSet['time'] = pd.to_datetime(DataSet["time"], unit='s')
                
                if len(The_Dataset) == 0 or The_Dataset['time'].iloc[-1] != DataSet['time'].iloc[-1]:
                    print_and_logging_Function("info", f"Data {The_timeframe} successfully fetched", "title")
                    return DataSet
                
                await asyncio.sleep(30)
            return pd.DataFrame()
        
        except Exception as e:
            print_and_logging_Function("error", f"Failed to fetch data: {e}", "title")
            raise RuntimeError(f"Failed to fetch data: {e}")

    async def main_fetching_data_Function(self, atimeframe = 'M15', aDataset: pd.DataFrame = pd.DataFrame()) -> pd.DataFrame:
        """
        Asynchronous function to fetch trading data for a specified timeframe.
        This function initializes the MetaTrader 5 (MT5) connection, logs in, and fetches 
        trading data for the specified timeframe. It also logs the process and handles 
        any exceptions that may occur during execution.
        Args:
            atimeframe (str, optional): The timeframe for which to fetch data. 
                Defaults to 'M15' (15-minute candles).
            aDataset (pd.DataFrame, optional): A pandas DataFrame to be used as input 
                for fetching data. Defaults to an empty DataFrame.
        Returns:
            pd.DataFrame: A pandas DataFrame containing the fetched trading data. 
            If an error occurs, an empty DataFrame is returned.
        Functionality:
            1. Initializes the MT5 connection by calling `initialize_mt5_Function`.
            2. Logs into MT5 by calling `login_mt5_Function`.
            3. Logs the start of the data fetching process.
            4. Fetches the trading data by calling `fetch_data_Function` with the 
               specified timeframe and dataset.
            5. Logs the details of the fetched data, including the number of candles 
               and the time range.
            6. Handles any exceptions that occur during the process and logs the error.
            7. Returns the fetched data as a pandas DataFrame, or an empty DataFrame 
               in case of an error.
        """
        
        try:
            await self.initialize_mt5_Function()
            await self.login_mt5_Function()
            print_and_logging_Function("info",  f"Fetching {atimeframe} Data...", "description")
            The_data = await self.fetch_data_Function(atimeframe, aDataset)
            if len(The_data) > 0:
                print_and_logging_Function("info", f"10000 candles in {atimeframe} fetched from {The_data['time'][0]} to {The_data['time'][len(The_data['time']) - 1]}", "description")
            return The_data
        except Exception as The_error:
            print_and_logging_Function("error", f"An error occurred in main_fetching_data: {The_error}", "title")
            return pd.DataFrame()
        # finally:
        #     mt.shutdown()

CMetatrader_Module = Metatrader_Module_Class()