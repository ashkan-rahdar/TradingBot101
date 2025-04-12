import mysql.connector  # noqa: F401
from mysql.connector import pooling
import sys
import os
import datetime
import aiomysql

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag_Class
from functions.logger import print_and_logging_Function
from classes.FlagPoint import FlagPoint_Class
from classes.DP_Parameteres import DP_Parameteres_Class

class Database_Class:
    """
    A utility class for managing database operations related to a trading bot.

    Attributes:
        connection_pool (pooling.MySQLConnectionPool): A connection pool for managing MySQL database connections.
        db_pool (aiomysql.Pool): Asynchronous database connection pool, initialized to None.

    Methods:
        __init__(The_timeframe: str):
            Initializes the class with the specified timeframe and sets up the necessary database tables.
        _initialize_tables_Function():
            Creates the required database tables if they do not already exist.
        initialize_db_pool_Function():
            Asynchronously initializes the database connection pool.
        save_flags_Function(flag_list: list[Flag_Class]):
            Asynchronously batch inserts multiple flags into the database, ensuring all dependencies are stored correctly.
        _update_dp_weights_Function(dps_to_update: list):
            Asynchronously updates the weights of decision points in the database.
        _get_tradeable_DPs_Function() -> list[tuple[DP_Parameteres_Class, str]]:
            Asynchronously fetches tradeable decision points (DPs) with a weight greater than 0 that are not already traded.
        _insert_positions_batch(positions: list[tuple[str, str, float, float, float, datetime.datetime, int, int, float]]):
            Asynchronously inserts a batch of trading position records into the database.
    """
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="tradingbot_pool",
        pool_size=10,  # Adjust based on your workload
        host="localhost",
        user="TradingBot",
        password="Nama-123456",
        database="tradingbotdb"
    )
    def __init__(self, The_timeframe: str):
        """
        Initializes the Database class with the specified timeframe and sets up the necessary database tables.
        Args:
            The_timeframe (str): The timeframe for which the database is being initialized. 
                                 This value is used to create table names specific to the timeframe.
        Attributes:
            flag_points_table_name (str): Name of the table for storing flag points data.
            important_dps_table_name (str): Name of the table for storing important decision points data.
            flags_table_name (str): Name of the table for storing flags data.
            Positions_table_name (str): Name of the table for storing positions data.
            TimeFrame (str): The timeframe associated with this database instance.
            detected_flags (int): Counter for the number of detected flags, initialized to 0.
            Traded_DP_Set (set): A set to track traded decision points.
            db_pool: Placeholder for the database connection pool, initialized to None.
        Raises:
            Exception: If the initialization of database tables fails, an error is logged.
        Side Effects:
            Logs information about the initialization process and any errors encountered.
        """
        self.flag_points_table_name = f"Flag_Points_{The_timeframe}"
        self.important_dps_table_name = f"Important_DPs_{The_timeframe}"
        self.flags_table_name = f"Flags_{The_timeframe}"
        self.Positions_table_name = f"Positions_{The_timeframe}"
        self.TimeFrame = The_timeframe
        self.detected_flags = 0
        self.Traded_DP_Set = set()
        self.db_pool = None
        print_and_logging_Function("info", f"Database for {The_timeframe} initialized.", "description")
        
        try:
            self._initialize_tables_Function()
        except Exception as e:
            print_and_logging_Function("error", f"Database initialization failed: {e}", "title")

    def _initialize_tables_Function(self):     
        queries = [
            f"""
            CREATE TABLE IF NOT EXISTS {self.flag_points_table_name} (
                id VARCHAR(255) PRIMARY KEY,
                price FLOAT NULL,
                time DATETIME NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.important_dps_table_name} (
                id VARCHAR(255) PRIMARY KEY,
                type ENUM('FTC', 'EL', 'MPL') NULL,
                High_Point VARCHAR(255) NULL,
                Low_Point VARCHAR(255) NULL,
                weight FLOAT NULL,
                first_valid_trade_time DATETIME NOT NULL,
                trade_direction ENUM('Bullish', 'Bearish', 'Undefined') NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.flags_table_name} (
                Unique_Point DATETIME NOT NULL PRIMARY KEY,
                type ENUM('Bullish', 'Bearish', 'Undefined') NOT NULL,
                High VARCHAR(255) NOT NULL,
                Low VARCHAR(255) NOT NULL,
                Starting_time DATETIME NOT NULL,
                Ending_time DATETIME NOT NULL,
                FTC VARCHAR(255),
                EL VARCHAR(255),
                MPL VARCHAR(255),
                weight FLOAT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.Positions_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Traded_DP VARCHAR(255),
                Order_type ENUM('Buy', 'Sell', 'Buy Limit', 'Sell Limit') NOT NULL,
                Price FLOAT NOT NULL,
                SL FLOAT NOT NULL,
                TP FLOAT NOT NULL,
                Last_modified_time DATETIME NOT NULL,
                Vol FLOAT Not Null,
                Order_ID INT Not Null,
                Result FLOAT NOT Null DEFAULT 0
            )
            """
        ]
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                conn.commit()
            print_and_logging_Function("info", f"{self.TimeFrame} Tables created successfully!", "title")
        except Exception as e:
            print_and_logging_Function("error", f"Couldn't initialize DB: {e}", "title")

    async def initialize_db_pool_Function(self):
        if self.db_pool is None:
            try:
                self.db_pool = await aiomysql.create_pool(
                    host="localhost",
                    user="TradingBot",
                    password="Nama-123456",
                    db="tradingbotdb",
                    minsize=5,
                    maxsize=20)
            except Exception as e:
                print_and_logging_Function("error", f"Error in initializing DP pool: {e}", "title")

    async def save_flags_Function(self, flag_list: list[Flag_Class]):
        """
        Batch insert multiple flags into the database, ensuring all dependencies are stored correctly.
        This function handles the insertion of flags and their associated data points (e.g., High, Low, FTC, EL, MPL) 
        into the database. It ensures that all related data is inserted in a transactional manner, maintaining data 
        integrity and avoiding partial updates.
        Args:
            flag_list (list[Flag_Class]): A list of Flag_Class objects to be saved in the database. Each flag contains 
                                          associated data points such as High, Low, FTC, EL, and MPL.
        Raises:
            Exception: If any error occurs during the database operations, the transaction is rolled back, and the 
                       exception is logged.
        Notes:
            - The function initializes the database connection pool if not already initialized.
            - It uses transactions to ensure atomicity of the batch insert operations.
            - Duplicate entries are handled using `ON DUPLICATE KEY UPDATE` to avoid inserting duplicate records.
            - The function updates the `detected_flags` attribute with the count of newly inserted flags.
            - The function commits changes to the database after each batch insert operation.
        """
        await self.initialize_db_pool_Function()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await conn.begin()  # Start transaction
                    flag_values = []
                    Important_DPs_values = []
                    flag_point_values = []
                    for flag in flag_list:
                        high_id = flag.high.ID_generator_Function()
                        low_id = flag.low.ID_generator_Function()
                        ftc_id = flag.FTC.ID_generator_Function() if flag.FTC else None
                        el_id = flag.EL.ID_generator_Function() if flag.EL else None
                        mpl_id = flag.MPL.ID_generator_Function() if flag.MPL else None

                        # Flag
                        flag_values.append((
                            flag.Unique_point, flag.flag_type, high_id, low_id, 
                            flag.Start_time, flag.End_time, ftc_id, el_id, mpl_id, flag.weight
                        ))

                        # High Point
                        if flag.high.ID_generator_Function() is not None:
                            flag_point_values.append((
                                flag.high.ID_generator_Function(), flag.high.price, flag.high.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))

                        # Low Point
                        if flag.low.ID_generator_Function() is not None:
                            flag_point_values.append((
                                flag.low.ID_generator_Function(), flag.low.price, flag.low.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))

                        # FTC
                        if flag.FTC.ID_generator_Function() is not None:
                            Important_DPs_values.append((
                                flag.FTC.ID_generator_Function(), flag.FTC.type, flag.FTC.High.ID_generator_Function(), flag.FTC.Low.ID_generator_Function(),
                                flag.FTC.weight, flag.FTC.first_valid_trade_time, flag.FTC.trade_direction 
                            ))
                            flag_point_values.append((
                                flag.FTC.High.ID_generator_Function(), flag.FTC.High.price, flag.FTC.High.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))
                            flag_point_values.append((
                                flag.FTC.Low.ID_generator_Function(), flag.FTC.Low.price, flag.FTC.Low.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))
                        
                        # EL
                        if flag.EL.ID_generator_Function() is not None:
                            Important_DPs_values.append((
                                flag.EL.ID_generator_Function(), flag.EL.type, flag.EL.High.ID_generator_Function(), flag.EL.Low.ID_generator_Function(),
                                flag.EL.weight, flag.EL.first_valid_trade_time, flag.EL.trade_direction 
                            ))
                            flag_point_values.append((
                                flag.EL.High.ID_generator_Function(), flag.EL.High.price, flag.EL.High.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))
                            flag_point_values.append((
                                flag.EL.Low.ID_generator_Function(), flag.EL.Low.price, flag.EL.Low.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))

                        # MPL
                        if flag.MPL.ID_generator_Function() is not None:
                            Important_DPs_values.append((
                                flag.MPL.ID_generator_Function(), flag.MPL.type, flag.MPL.High.ID_generator_Function(), flag.MPL.Low.ID_generator_Function(),
                                flag.MPL.weight, flag.MPL.first_valid_trade_time, flag.MPL.trade_direction 
                            ))
                            flag_point_values.append((
                                flag.MPL.High.ID_generator_Function(), flag.MPL.High.price, flag.MPL.High.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))
                            flag_point_values.append((
                                flag.MPL.Low.ID_generator_Function(), flag.MPL.Low.price, flag.MPL.Low.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))

                    await cursor.execute(f"SELECT COUNT(*) FROM {self.flags_table_name}")
                    before_insert_count = await cursor.fetchone()
                    before_insert_count = before_insert_count[0] 

                    await cursor.executemany(
                        f"""INSERT INTO {self.flags_table_name} 
                            (Unique_Point, type, High, Low, Starting_time, Ending_time, FTC, EL, MPL, weight)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE Unique_Point = Unique_Point""",
                        flag_values
                    )
                    await conn.commit()
                    
                    await cursor.execute(f"SELECT COUNT(*) FROM {self.flags_table_name}")
                    after_insert_count = await cursor.fetchone()
                    after_insert_count = after_insert_count[0]
                    self.detected_flags = after_insert_count - before_insert_count

                    await cursor.executemany(
                        f"""INSERT INTO {self.important_dps_table_name} 
                            (id, type, High_Point, Low_Point, weight, first_valid_trade_time, trade_direction)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE id = id""",
                        Important_DPs_values
                    )
                    await conn.commit()

                    await cursor.executemany(
                        f"""INSERT INTO {self.flag_points_table_name} 
                            (id, price, time)  -- ✅ FIXED: Explicitly include `id`
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE id = id""",
                        flag_point_values
                    )
                    await conn.commit()


                except Exception as e:
                    await conn.rollback()
                    print_and_logging_Function("error", f"Error batch saving flags: {e}", "title")

    async def _update_dp_weights_Function(self, dps_to_update: list):
        """
        Asynchronously updates the weights of data points (DPs) in the database.
        This function performs a batch update on the specified table to modify the 
        weights of multiple data points based on their IDs.
        Args:
            dps_to_update (list): A list of tuples where each tuple contains:
                - dp_id (int): The ID of the data point to update.
                - weight (float): The new weight value to set for the data point.
        Raises:
            Exception: If an error occurs during the database operation, it logs the 
            error and rolls back the transaction.
        Notes:
            - The function uses a connection pool (`self.db_pool`) to acquire a database 
              connection and execute the batch update.
            - The table name is specified by `self.important_dps_table_name`.
            - The transaction is committed if successful, or rolled back in case of an error.
        """
        
        try:
            # Prepare the SQL query and values
            query = f"UPDATE {self.important_dps_table_name} SET weight = %s WHERE id = %s"
            values = [(weight, dp_id) for dp_id, weight in dps_to_update]

            # Execute the batch update
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.executemany(query, values)  # Perform the batch update
                    await conn.commit()  # Commit the transaction
        except Exception as e:
            print_and_logging_Function("error", f"Error in batch updating DP weights: {e}", "title")
            await conn.rollback()  # Rollback if there's an error

    async def _get_tradeable_DPs_Function(self) -> list[tuple[DP_Parameteres_Class, str]]:
        """
        Asynchronously fetches tradeable Decision Points (DPs) from the database.
        This function retrieves all important DPs with a weight greater than 0, 
        along with their associated flag points (if any), and filters out DPs 
        that have already been traded (exist in the Positions table). It then 
        constructs and returns a list of DP objects paired with their IDs.
        Returns:
            list[tuple[DP_Parameteres_Class, str]]: A list of tuples where each tuple 
            contains a DP_Parameteres_Class object representing a tradeable DP and 
            its corresponding ID.
        Raises:
            Exception: Logs and handles any exceptions that occur during the database 
            operations.
        Notes:
            - The function uses a connection pool (`db_pool`) to interact with the database.
            - Flag points are fetched in bulk for efficiency and stored in a dictionary 
              for quick lookup.
            - The function ensures that no duplicate DPs are returned by checking against 
              the Positions table.
        Database Tables:
            - `important_dps_table_name`: Stores the important DPs with their attributes.
            - `flag_points_table_name`: Stores the flag points associated with DPs.
            - `Positions_table_name`: Stores the traded DPs to avoid duplication.
        Example Workflow:
            1. Fetch all DPs with weight > 0 from the `important_dps_table_name`.
            2. Retrieve associated flag points (High_Point and Low_Point) from 
               `flag_points_table_name`.
            3. Exclude DPs that already exist in the `Positions_table_name`.
            4. Construct DP_Parameteres_Class objects for the remaining DPs and 
               return them along with their IDs.
        """
        
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Get all important DPs where weight > 0
                    await cursor.execute(f"""
                        SELECT id, type, High_Point, Low_Point, weight, first_valid_trade_time, trade_direction 
                        FROM {self.important_dps_table_name} WHERE weight > 0
                    """)
                    dp_results = await cursor.fetchall()

                    # Prepare the list of flag_ids from High_Point and Low_Point
                    flag_ids = [row[2] for row in dp_results if row[2]] + [row[3] for row in dp_results if row[3]]

                    flag_points = {}
                    if flag_ids:
                        # Fetch all flag points in one go
                        await cursor.execute(f"""
                            SELECT id, price, time FROM {self.flag_points_table_name} WHERE id IN ({','.join(['%s'] * len(flag_ids))})
                        """, flag_ids)
                        # Create a dictionary for fast lookup
                        flag_points = {str(row[0]): FlagPoint_Class(price=row[1], time=row[2]) for row in await cursor.fetchall()}

                    # Get existing traded dp ids to avoid duplication
                    existing_dp_ids = set()
                    await cursor.execute(f"""
                        SELECT DISTINCT Traded_DP FROM {self.Positions_table_name}
                    """)
                    existing_dp_ids = {row[0] for row in await cursor.fetchall()}

                    # Build DP objects and return them, only for DPs that are not already in the Positions table
                    dps = []
                    for row in dp_results:
                        dp_id, dp_type, high_id, low_id, weight, first_valid_time, trade_direction = row
                        if dp_id in existing_dp_ids:
                            continue  # Skip DP if it already exists in the Positions table
                        
                        high_point = flag_points.get(str(high_id)) if high_id else None
                        low_point = flag_points.get(str(low_id)) if low_id else None
                        dp = DP_Parameteres_Class(
                            type=dp_type, 
                            High=high_point, 
                            Low=low_point, 
                            weight=weight, 
                            first_valid_trade_time=first_valid_time, 
                            trade_direction=trade_direction
                        )
                        dps.append((dp, dp_id))

                    return dps
        except Exception as e:
            print_and_logging_Function("error", f"Error in fetching tradeable DPs: {e}", "title")
            return []
  
    async def _insert_positions_batch(self, positions: list[tuple[str, str, float, float, float, datetime.datetime, int, int, float]]):
        """
        Asynchronously inserts a batch of trading position records into the database.
        This method performs a batch insert of trading positions into the specified database table.
        If a record with the same primary key already exists, the `ON DUPLICATE KEY UPDATE` clause
        ensures that no changes are made to the existing record.
        Args:
            positions (list[tuple[str, str, float, float, float, datetime.datetime, int, int, float]]): 
                A list of tuples, where each tuple represents a trading position with the following fields:
                - Traded_DP (str): The traded data point.
                - Order_type (str): The type of order (e.g., "buy" or "sell").
                - Price (float): The price at which the trade was executed.
                - SL (float): The stop-loss value.
                - TP (float): The take-profit value.
                - Last_modified_time (datetime.datetime): The last modification timestamp of the position.
                - Vol (int): The volume of the trade.
                - Order_ID (int): The unique identifier for the order.
                - Result (float): The result or outcome of the trade.
        Returns:
            None: This function does not return a value. It commits the transaction to the database.
        Raises:
            Exception: If an error occurs during the database operation, an exception is raised with
                       a descriptive error message.
        """
        # Validate input (we assume positions are already validated)
        if not positions:
            return

        # Prepare the SQL query
        query = f"""
            INSERT INTO {self.Positions_table_name} 
            (Traded_DP, Order_type, Price, SL, TP, Last_modified_time, Vol, Order_ID, Result)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE Traded_DP = Traded_DP
        """

        # Perform the batch insert
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Execute the batch insert using executemany
                    await cursor.executemany(query, positions)

                    # Commit the transaction
                    await conn.commit()
                    return
        except Exception as e:
            raise Exception(f"Error inserting batch positions: {e}")
