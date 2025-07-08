import mysql.connector  # noqa: F401
from mysql.connector import pooling
import sys
import os
import datetime
import aiomysql
import pandas as pd
import typing

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag_Class
from functions.logger import print_and_logging_Function
from classes.FlagPoint import FlagPoint_Class
from classes.DP_Parameteres import DP_Parameteres_Class
from classes.Metatrader_Module import CMetatrader_Module

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
        pool_size=12,  # Adjust based on your workload
        host="localhost",
        user="TradingBot",
        password="Nama-123456",
        database="tradingbotdb",
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
        self.Traded_DP_Dict: dict[str, TradeInfo] = {}
        self.db_pool = None
        print_and_logging_Function("info", f"{self.TimeFrame} -> Database for {The_timeframe} initialized.", "description")
        
        try:
            self._initialize_tables_Function()
        except Exception as e:
            print_and_logging_Function("error", f"{self.TimeFrame} -> Database initialization failed: {e}", "title")

    def _initialize_tables_Function(self):
        # in here I haven't used "FOREIGN KEY" due to I would insert tables using batch and table by table
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
                High_Point VARCHAR(255),
                Low_Point VARCHAR(255),
                weight FLOAT NULL,
                first_valid_trade_time DATETIME NOT NULL,
                trade_direction ENUM('Bullish', 'Bearish', 'Undefined') NULL,
                length FLOAT NULL,
                Flag_Ratio FLOAT NULL,
                NO_Used_Candles INT NULL,
                Used_Ratio FLOAT NULL,
                Related_DP_1 VARCHAR(255) NULL,
                Related_DP_2 VARCHAR(255) NULL,
                Is_related_DP_used BOOL DEFAULT FALSE,
                Is_golfed BOOL DEFAULT FALSE,
                Is_used_half BOOL DEFAULT FALSE,
                parent_length INT NULL,
                Result FLOAT NOT NULL DEFAULT 0
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
                MPL VARCHAR(255)
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
                Vol FLOAT NOT NULL,
                Order_ID INT NOT NULL UNIQUE,
                Probability INT NOT NULL,
                Result FLOAT NOT NULL DEFAULT 0
            )
            """
        ]

        # Triggers must be separate because they use BEGIN..END
        trigger_queries = [
            f"""
            CREATE TRIGGER trg_update_position_result
            AFTER UPDATE ON {self.important_dps_table_name}
            FOR EACH ROW
            BEGIN
                IF NEW.Result <> OLD.Result THEN
                    UPDATE {self.Positions_table_name}
                    SET Result = NEW.Result * ABS(Price - SL)
                    WHERE Traded_DP = NEW.id AND Result <> NEW.Result;
                END IF;
            END
            """
        ]

        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)

                # MySQL requires each trigger to be created individually
                for trigger in trigger_queries:
                    try:
                        cursor.execute(f"DROP TRIGGER IF EXISTS {trigger.split()[2]}")
                        cursor.execute(trigger)
                    except Exception as e:
                        print_and_logging_Function("warning", f"{self.TimeFrame} -> Trigger creation failed: {e}", "title")

                conn.commit()
                print_and_logging_Function("info", f"{self.TimeFrame} -> Tables and triggers created successfully!", "title")
        except Exception as e:
            print_and_logging_Function("error", f"{self.TimeFrame} -> Couldn't initialize DB: {e}", "title")

    async def initialize_db_pool_Function(self):
        if self.db_pool is None:
            try:
                self.db_pool = await aiomysql.create_pool(
                    host="localhost",
                    user="TradingBot",
                    password="Nama-123456",
                    db="tradingbotdb",
                    autocommit=True,
                    minsize=5,
                    maxsize=20)
            except Exception as e:
                print_and_logging_Function("error", f"{self.TimeFrame} -> Error in initializing DP pool: {e}", "title")

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
        async with self.db_pool.acquire() as conn: # type: ignore
            await conn.commit()  # Ensure previous state is clean (optional but safe)
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
                            flag.Start_time, flag.End_time, ftc_id, el_id, mpl_id
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
                            if len(flag.FTC.related_DP_indexes)== 0: 
                                related_DP_1 = None
                                related_DP_2 = None
                            else:
                                related_DP_1 = flag.FTC.related_DP_indexes[0]
                                related_DP_2 = flag.FTC.related_DP_indexes[1]
                                    
                            Important_DPs_values.append((
                                flag.FTC.ID_generator_Function(), flag.FTC.type, flag.FTC.High.ID_generator_Function(), flag.FTC.Low.ID_generator_Function(),
                                flag.FTC.weight, flag.FTC.first_valid_trade_time, flag.FTC.trade_direction, flag.FTC.length,
                                flag.FTC.ratio_to_flag, flag.FTC.number_used_candle, flag.FTC.used_ratio, related_DP_1, related_DP_2, int(flag.FTC.Is_related_DP_used),
                                int(flag.FTC.Is_golfed), int(flag.FTC.Is_used_half), flag.FTC.parent_length
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
                                flag.EL.weight, flag.EL.first_valid_trade_time, flag.EL.trade_direction, flag.EL.length,
                                flag.EL.ratio_to_flag, flag.EL.number_used_candle, flag.EL.used_ratio, flag.EL.related_DP_indexes[0], None, int(flag.EL.Is_related_DP_used),
                                int(flag.EL.Is_golfed), int(flag.EL.Is_used_half), flag.EL.parent_length
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
                                flag.MPL.weight, flag.MPL.first_valid_trade_time, flag.MPL.trade_direction, flag.MPL.length,
                                flag.MPL.ratio_to_flag, flag.MPL.number_used_candle, flag.MPL.used_ratio, None, None, int(flag.MPL.Is_related_DP_used),
                                int(flag.MPL.Is_golfed), int(flag.MPL.Is_used_half), flag.MPL.parent_length
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
                            (Unique_Point, type, High, Low, Starting_time, Ending_time, FTC, EL, MPL)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                            (id, type, High_Point, Low_Point, weight, first_valid_trade_time, trade_direction, length, 
                            Flag_Ratio, NO_Used_Candles, Used_Ratio, Related_DP_1, Related_DP_2, Is_related_DP_used,
                            Is_golfed, Is_used_half, parent_length)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    print_and_logging_Function("error", f"{self.TimeFrame} -> Error batch saving flags: {e}", "title")

    async def _update_dp_weights_Function(self, dps_to_update: list):
        """
        Asynchronously updates the weights of data points (DPs) in the database.
        This function performs a batch update on the specified table to modify the 
        weights of multiple data points based on their IDs.
        Args:
            dps_to_update (list): A list of tuples where each tuple contains:
                - dp_id (str): The ID of the data point to update.
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
            async with self.db_pool.acquire() as conn: # type: ignore
                await conn.commit()  # Ensure previous state is clean (optional but safe)
                async with conn.cursor() as cursor:
                    await cursor.executemany(query, values)  # Perform the batch update
                    await conn.commit()  # Commit the transaction
        except Exception as e:
            print_and_logging_Function("error", f"{self.TimeFrame} -> Error in batch updating DP weights: {e}", "title")
            await conn.rollback()  # type: ignore # Rollback if there's an error

    async def _update_dp_Results_Function(self, dps_to_update: list):
        """
        Asynchronously updates the Result of data points (DPs) in the database.
        This function performs a batch update on the specified table to modify the 
        Results of multiple data points based on their IDs.
        Args:
            dps_to_update (list): A list of tuples where each tuple contains:
                - dp_id (str): The ID of the data point to update.
                - Result (float): The new Result value to set for the data point.
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
            query = f"UPDATE {self.important_dps_table_name} SET Result = %s WHERE id = %s"
            values = [(Result, dp_id) for dp_id, Result in dps_to_update]

            # Execute the batch update
            async with self.db_pool.acquire() as conn: # type: ignore
                await conn.commit()  # Ensure previous state is clean (optional but safe)                
                async with conn.cursor() as cursor:
                    await cursor.executemany(query, values)  # Perform the batch update
                    await conn.commit()  # Commit the transaction
        except Exception as e:
            print_and_logging_Function("error", f"{self.TimeFrame} -> Error in batch updating DP Results: {e}", "title")
            await conn.rollback()  # type: ignore # Rollback if there's an error
            
    async def _get_update_DPlist_Function(self) -> list[tuple[DP_Parameteres_Class, str]]:
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
            async with self.db_pool.acquire() as conn: # type: ignore
                await conn.commit()  # Ensure previous state is clean (optional but safe)
                async with conn.cursor() as cursor:
                    # Step 1: Get important DPs
                    await cursor.execute(f"""
                        SELECT id, type, High_Point, Low_Point, weight, first_valid_trade_time, trade_direction,
                            length, Flag_Ratio, NO_Used_Candles, Used_Ratio, Related_DP_1, Related_DP_2,
                            Is_related_DP_used, Is_golfed, Is_used_half, parent_length
                        FROM {self.important_dps_table_name}
                        WHERE weight > 0
                    """)
                    dp_columns = [desc[0] for desc in cursor.description]
                    dp_results = await cursor.fetchall()

                    # Step 2: Fetch Flag Points
                    flag_ids = [row[2] for row in dp_results if row[2]] + [row[3] for row in dp_results if row[3]]
                    flag_points = {}
                    if flag_ids:
                        await cursor.execute(f"""
                            SELECT id, price, time 
                            FROM {self.flag_points_table_name} 
                            WHERE id IN ({','.join(['%s'] * len(flag_ids))})
                        """, flag_ids)
                        flag_points = {str(row[0]): FlagPoint_Class(price=row[1], time=row[2]) for row in await cursor.fetchall()}

                    # Step 3: Fetch existing traded DPs
                    await cursor.execute(f"SELECT Traded_DP, TP, Vol, Order_ID FROM {self.Positions_table_name}")
                    rows = await cursor.fetchall()
                    self.Traded_DP_Dict = {
                        row[0]: {"TP": row[1], "Vol": row[2], "Order_ID": row[3]} for row in rows
                    }

                    # Step 4: Fetch id -> Result mapping
                    await cursor.execute(f"""
                        SELECT id, Result
                        FROM {self.important_dps_table_name}
                        WHERE Result != 0
                    """)
                    result_columns = [desc[0] for desc in cursor.description]
                    rows = await cursor.fetchall()
                    full_df = pd.DataFrame(rows, columns=result_columns)
                    id_to_result = dict(zip(full_df['id'], full_df['Result']))

                    # Step 5: Replace Related_DP_1 and Related_DP_2
                    updated_dp_results = []
                    for row in dp_results:
                        row = dict(zip(dp_columns, row))
                        if row.get('Related_DP_1') in id_to_result:
                            row['Related_DP_1'] = id_to_result[row['Related_DP_1']]
                        else:
                            row['Related_DP_1'] = None
                        if row.get('Related_DP_2') in id_to_result:
                            row['Related_DP_2'] = id_to_result[row['Related_DP_2']]
                        else:
                            row['Related_DP_2'] = None
                        updated_dp_results.append(row)

                    # Step 6: Build DP objects
                    dps = []
                    for row in updated_dp_results:
                        dp_id = row['id']
                        # if dp_id in self.Traded_DP_Set:  // in this way we let the code update everything of a traded DP and just not trading it again!
                        #     continue  # Already exists

                        high_point = flag_points.get(str(row['High_Point'])) if row['High_Point'] else None
                        low_point = flag_points.get(str(row['Low_Point'])) if row['Low_Point'] else None
                        dp = DP_Parameteres_Class(
                            type=row['type'], 
                            High=high_point,  # type: ignore
                            Low=low_point,  # type: ignore
                            weight=row['weight'], 
                            first_valid_trade_time=row['first_valid_trade_time'], 
                            trade_direction=row['trade_direction']
                        )
                        dp.length = row['length']
                        dp.ratio_to_flag = row['Flag_Ratio']
                        dp.number_used_candle = row['NO_Used_Candles']
                        dp.used_ratio = row['Used_Ratio']                            
                        dp.Is_related_DP_used = row['Is_related_DP_used']
                        dp.Is_golfed = row['Is_golfed']
                        dp.Is_used_half = row['Is_used_half']
                        dp.parent_length = row['parent_length']
                        dp.related_DP_indexes.append(row['Related_DP_1'])
                        dp.related_DP_indexes.append(row['Related_DP_2'])

                        dps.append((dp, dp_id))

                    return dps
        except Exception as e:
            print_and_logging_Function("error", f"{self.TimeFrame} -> Error in fetching tradeable DPs: {e}", "title")
            return []
    
    async def _get_tradeable_DPs_Function(self, dp_ids: list[str]) -> list[DP_Parameteres_Class]:
        """
        Given a list of important-DP IDs, load their full parameters (including
        substituted Related_DP_1/2 Results) and return a list of DP_Parameteres_Class.
        """
        if not dp_ids:
            return []

        try:
            async with self.db_pool.acquire() as conn: # type: ignore
                await conn.commit()  # Ensure previous state is clean (optional but safe)
                async with conn.cursor() as cursor:
                    # 1) Fetch the requested DP rows
                    sql = f"""
                        SELECT id, type, High_Point, Low_Point, weight, first_valid_trade_time,
                               trade_direction, length, Flag_Ratio, NO_Used_Candles,
                               Used_Ratio, Related_DP_1, Related_DP_2,
                               Is_related_DP_used, Is_golfed, Is_used_half, parent_length
                        FROM {self.important_dps_table_name}
                        WHERE id IN ({','.join(['%s']*len(dp_ids))})
                    """
                    await cursor.execute(sql, dp_ids)
                    dp_columns = [c[0] for c in cursor.description]
                    dp_rows = await cursor.fetchall()
                    if not dp_rows:
                        return []

                    # 2) Build id -> Result map for ALL non-zero Results
                    await cursor.execute(f"""
                        SELECT id, Result
                        FROM {self.important_dps_table_name}
                        WHERE Result != 0
                    """)
                    res_rows = await cursor.fetchall()
                    id_to_result = {r[0]: r[1] for r in res_rows}

                    # 3) Collect all High_Point/Low_Point IDs for flag lookup
                    flag_ids = []
                    for row in dp_rows:
                        hp, lp = row[2], row[3]
                        if hp: 
                            flag_ids.append(hp)
                        if lp: 
                            flag_ids.append(lp)
                    flag_ids = list(set(flag_ids))
                    flag_points = {}
                    if flag_ids:
                        sql_fp = f"""
                            SELECT id, price, time
                            FROM {self.flag_points_table_name}
                            WHERE id IN ({','.join(['%s']*len(flag_ids))})
                        """
                        await cursor.execute(sql_fp, flag_ids)
                        for fid, price, when in await cursor.fetchall():
                            flag_points[fid] = FlagPoint_Class(price=price, time=when)

                    # 4) Substitute Related_DP_1/2 → actual Result or None
                    updated = []
                    for row in dp_rows:
                        rec = dict(zip(dp_columns, row))
                        for fld in ('Related_DP_1','Related_DP_2'):
                            rid = rec[fld]
                            rec[fld] = id_to_result.get(rid) if rid in id_to_result else None
                        updated.append(rec)

                    # 5) Build DP_Parameteres_Class objects
                    results = []
                    for rec in updated:
                        dp = DP_Parameteres_Class(
                            type=rec['type'],
                            High=flag_points.get(rec['High_Point']), # type: ignore
                            Low =flag_points.get(rec['Low_Point']), # type: ignore
                            weight=rec['weight'],
                            first_valid_trade_time=rec['first_valid_trade_time'],
                            trade_direction=rec['trade_direction']
                        )
                        # assign numeric/flag fields
                        dp.length              = rec['length']
                        dp.ratio_to_flag       = rec['Flag_Ratio']
                        dp.number_used_candle  = rec['NO_Used_Candles']
                        dp.used_ratio          = rec['Used_Ratio']
                        dp.Is_related_DP_used  = rec['Is_related_DP_used']
                        dp.Is_golfed           = rec['Is_golfed']
                        dp.Is_used_half        = rec['Is_used_half']
                        dp.parent_length       = rec['parent_length']
                        # append the substituted Result‐values for related DPs
                        dp.related_DP_indexes.append(rec['Related_DP_1'])
                        dp.related_DP_indexes.append(rec['Related_DP_2'])

                        results.append(dp)

                    return results

        except Exception as e:
            print_and_logging_Function(
                "error",
                f"{self.TimeFrame} -> Error in fetch_DPs_by_id for IDs {dp_ids}: {e}",
                "title"
            )
            return []

    async def _insert_positions_batch(self, positions: list[tuple[str, str, float, float, float, datetime.datetime, int, int, int, float]]):
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
        if not positions:
            return

        # Step 1: Extract Traded_DP list
        traded_dps = [pos[0] for pos in positions]
        placeholders = ', '.join(['%s'] * len(traded_dps))
        check_query = f"""
            SELECT Traded_DP, Order_ID FROM {self.Positions_table_name}
            WHERE Traded_DP IN ({placeholders})
        """

        try:
            async with self.db_pool.acquire() as conn:  # type: ignore
                await conn.commit()  # Ensure previous state is clean (optional but safe)
                async with conn.cursor() as cursor:
                    # Step 2: Check for existing Traded_DP entries
                    await cursor.execute(check_query, traded_dps)
                    existing : dict[str, int] = {row[0]: row[1] for row in await cursor.fetchall()}
                    
                    # Step 3: Filter positions to insert only new ones
                    new_positions = [pos for pos in positions if pos[0] not in existing.keys()]

                    # Step 4: Insert only non-duplicate positions
                    if new_positions:
                        insert_query = f"""
                            INSERT INTO {self.Positions_table_name} 
                            (Traded_DP, Order_type, Price, SL, TP, Last_modified_time, Vol, Order_ID, Probability, Result)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        await cursor.executemany(insert_query, new_positions)
                        await conn.commit()

                    # Step 5: Raise error if duplicates found and cancel duplicated positions !
                    if existing:
                        for anOrder_ID in existing.values():
                            CMetatrader_Module.cancel_order(anOrder_ID)
                        raise ValueError(f"Duplicate Traded_DP(s) already exist in DB: {', '.join(existing)}")

        except Exception as e:
            raise Exception(f"Error inserting batch positions: {e}")
        
    async def Read_ML_table_Function(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        try:
            async with self.db_pool.acquire() as conn: # type: ignore
                async with conn.cursor() as cursor:
                    # Fetch all rows
                    await cursor.execute(f"""
                        SELECT id, type, length, Flag_Ratio, NO_Used_Candles,
                            Used_Ratio, Related_DP_1, Related_DP_2, Is_related_DP_used,
                            Is_golfed, Is_used_half, parent_length, Result
                        FROM {self.important_dps_table_name}
                        WHERE Result != 0
                    """)
                    rows = await cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Convert to DataFrame
                    full_df = pd.DataFrame(rows, columns=columns)

                    # Build a dictionary for fast lookup of id -> Result
                    id_to_result = dict(zip(full_df['id'], full_df['Result']))

                    # Now, prepare the Related DP results
                    full_df['Related_DP_1'] = full_df['Related_DP_1'].apply(
                        lambda x: id_to_result.get(x, 0) if pd.notnull(x) else None
                    )
                    full_df['Related_DP_2'] = full_df['Related_DP_2'].apply(
                        lambda x: id_to_result.get(x, 0) if pd.notnull(x) else None
                    )

                    # Prepare Input and Output
                    FTC_full_df = full_df[full_df['type'] == 'FTC'].reset_index(drop=True)
                    # EL_full_df = full_df[full_df['type'] == 'EL'].reset_index(drop=True)
                    # MPL_full_df = full_df[full_df['type'] == 'MPL'].reset_index(drop=True)

                    FTC_Input = FTC_full_df.drop(columns=['Result', 'id', 'type'])
                    FTC_Output = FTC_full_df['Result']
                    
                    # EL_Input = EL_full_df.drop(columns=['Result', 'id', 'type'])
                    # EL_Output = EL_full_df['Result']
                    
                    # MPL_Input = MPL_full_df.drop(columns=['Result', 'id', 'type'])
                    # MPL_Output = MPL_full_df['Result']
                    
                    # return FTC_Input, FTC_Output, EL_Input, EL_Output, MPL_Input, MPL_Output
                    return FTC_Input, FTC_Output # type: ignore
        except Exception as e:
            print_and_logging_Function("error", f"{self.TimeFrame} -> Error in fetching ML Dataset: {e}", "title")
            return pd.DataFrame(), pd.DataFrame()
    
    async def Read_Pending_Positions_Function(self) -> dict[str, int]:
        if self.db_pool is None:
            await self.initialize_db_pool_Function()

        try:
            async with self.db_pool.acquire() as conn: # type: ignore
                await conn.commit()  # Ensure previous state is clean (optional but safe)
                async with conn.cursor() as cursor:
                    try:
                        await cursor.execute(f"""
                            SELECT Traded_DP, Order_ID
                            FROM {self.Positions_table_name}
                            WHERE Result = 0
                        """)
                        rows = await cursor.fetchall()
                        order_IDs = {row[0]: row[1] for row in rows}

                        # print_and_logging_Function("info", f"{self.TimeFrame} -> ID Open positions: {order_IDs.values()}", "description")
                        return order_IDs
                    except Exception as e:
                        raise e
                    finally:
                        await cursor.close()

        except Exception as e:
            print_and_logging_Function("error", f"{self.TimeFrame} -> Error in fetching open positions: {e}", "title")
            return {}

    async def remove_cancelled_positions_Function(self, cancelled_list_dict: dict[str, int]):
        if self.db_pool is None:
            await self.initialize_db_pool_Function()
        try:
            for cancelled_id in cancelled_list_dict.keys():
                self.Traded_DP_Dict.pop(cancelled_id, None)  # Safe removal

            values = list(cancelled_list_dict.values())
            if values:
                placeholders = ','.join(['%s'] * len(values))
                query = f"DELETE FROM {self.Positions_table_name} WHERE Order_ID IN ({placeholders})"
                async with self.db_pool.acquire() as conn:  # type: ignore
                    await conn.commit()  # Ensure previous state is clean (optional but safe)
                    async with conn.cursor() as cursor:
                        await cursor.execute(query, values)
                        await conn.commit()
                        print_and_logging_Function("info", f"{self.TimeFrame} -> Removed {values} cancelled positions from DB and memory.", "description")
        except Exception as e:
            raise Exception(f"Error in removing the cancelled positions from DB: {e}")
    
    async def correct_position_results_Function(self):
        if self.db_pool is None:
            await self.initialize_db_pool_Function()
            
        try:
            async with self.db_pool.acquire() as conn:  # type: ignore
                await conn.commit()
                async with conn.cursor() as cursor:

                    # Step 1: Read all necessary fields from Positions table
                    await cursor.execute(f"""
                        SELECT id, Traded_DP, Price, TP, SL, Result
                        FROM {self.Positions_table_name}
                    """)
                    positions = await cursor.fetchall()
                    if not positions:
                        return

                    # Step 2: Build a list of Traded_DP ids to query their weights
                    traded_dp_ids = list(set(row[1] for row in positions if row[1]))
                    await cursor.execute(f"""
                        SELECT id, weight
                        FROM {self.important_dps_table_name}
                        WHERE id IN ({','.join(['%s'] * len(traded_dp_ids))})
                    """, traded_dp_ids)
                    dp_weights_raw = await cursor.fetchall()
                    dp_weights = {row[0]: row[1] for row in dp_weights_raw}

                    # Step 3: Prepare update list
                    updates = []
                    for pos in positions:
                        pos_id, traded_dp, price, tp, sl, result = pos
                        
                        if result == 0:
                            continue  # Skip positions without a result yet

                        hit_tp = abs(tp - price)
                        hit_sl = abs(sl - price)

                        if result >= hit_tp:
                            corrected_result = hit_tp
                        elif dp_weights.get(traded_dp, 0) == 0:
                            corrected_result = -hit_sl
                        else:
                            continue  # The trade hasn't hit TP or SL, leave result unchanged

                        if corrected_result != result:
                            updates.append((corrected_result, pos_id))

                    # Step 4: Batch update the corrected Results
                    for new_result, pos_id in updates:
                        await cursor.execute(f"""
                            UPDATE {self.Positions_table_name}
                            SET Result = %s
                            WHERE id = %s
                        """, (new_result, pos_id))

                    await conn.commit()

        except Exception as e:
            raise Exception(f"Error correcting Results in Positions table: {e}")
  
    async def PNL_Calculator_Function(self) -> tuple[float, float]:
        try:
            async with self.db_pool.acquire() as conn:  # type: ignore
                await conn.commit()
                async with conn.cursor() as cursor:
                    await cursor.execute(f"""SELECT SUM(Result * Vol) FROM {self.Positions_table_name}""")
                    result = await cursor.fetchone()
                    total_vol_pip = result[0] if result and result[0] is not None else 0.0

            return CMetatrader_Module.profit_calculator_Function(total_vol_pip)
        except Exception as e:
            raise Exception(f"Error calculating the PNL of {self.Positions_table_name}: {e}")
        
    async def winrate_Calculator_Function(self) -> tuple[float, int]:
        if self.db_pool is None:
            await self.initialize_db_pool_Function()

        try:
            async with self.db_pool.acquire() as conn:  # type: ignore
                await conn.commit()
                async with conn.cursor() as cursor:
                    await cursor.execute(f"""
                        SELECT 
                            CAST(SUM(CASE WHEN Result > 0 THEN 1 ELSE 0 END) AS FLOAT) / 
                            NULLIF(COUNT(CASE WHEN Result != 0 THEN 1 END), 0) AS winrate,
                            COUNT(CASE WHEN Result != 0 THEN 1 END) AS trade_count
                        FROM {self.Positions_table_name}
                    """)
                    result = await cursor.fetchone()
                    winrate = result[0] if result and result[0] is not None else 0.0
                    trade_count = result[1] if result and result[1] is not None else 0
                    return winrate, trade_count
        except Exception as e:
            raise Exception(f"Error calculating the winrate of {self.Positions_table_name}: {e}")
        
    async def update_position_TPs_batch_Function(self, modifying_TP_DB: list[tuple[int, float]]) -> None:
        """
        Batch update TP values in the Positions table using (Traded_DP, New TP) pairs.

        Args:
            modifying_TP_DB: List of tuples where each tuple is (Traded_DP, new_TP)
        """
        if not modifying_TP_DB:
            return  # Nothing to update

        if self.db_pool is None:
            await self.initialize_db_pool_Function()

        try:
            async with self.db_pool.acquire() as conn:  # type: ignore
                await conn.commit()
                async with conn.cursor() as cursor:
                    await cursor.executemany(
                        f"""
                        UPDATE {self.Positions_table_name}
                        SET TP = %s
                        WHERE Order_ID = %s
                        """,
                        [(tp, order_id) for order_id, tp in modifying_TP_DB]
                    )
                    await conn.commit()
        except Exception as e:
            raise Exception(f"Error updating TP values in batch: {e}")

class TradeInfo(typing.TypedDict):
    TP: float
    Vol: float
    Order_ID: int