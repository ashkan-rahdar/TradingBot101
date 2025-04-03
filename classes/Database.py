import mysql.connector
from mysql.connector import pooling
import pandas as pd
import sys
import os
from colorama import Fore,Style
import datetime
import aiomysql

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag_Class
from functions.logger import print_and_logging_Function
from classes.FlagPoint import FlagPoint_Class
from classes.DP_Parameteres import DP_Parameteres_Class

class Database_Class:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="tradingbot_pool",
        pool_size=10,  # Adjust based on your workload
        host="localhost",
        user="TradingBot",
        password="Nama-123456",
        database="tradingbotdb"
    )
    def __init__(self, The_timeframe: str):
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
                id INT AUTO_INCREMENT PRIMARY KEY,
                Unique_Point DATETIME NOT NULL,
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
                Result INT NOT Null DEFAULT 0
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
        """Batch insert multiple flags, ensuring all dependencies are stored correctly."""
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
                        if flag.high.ID_generator_Function() != None:
                            flag_point_values.append((
                                flag.high.ID_generator_Function(), flag.high.price, flag.high.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))

                        # Low Point
                        if flag.low.ID_generator_Function() != None:
                            flag_point_values.append((
                                flag.low.ID_generator_Function(), flag.low.price, flag.low.time.strftime('%Y-%m-%d %H:%M:%S')
                            ))

                        # FTC
                        if flag.FTC.ID_generator_Function() != None:
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
                        if flag.EL.ID_generator_Function() != None:
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
                        if flag.MPL.ID_generator_Function() != None:
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
                    await cursor.executemany(
                        f"""INSERT INTO {self.flags_table_name} 
                            (Unique_Point, type, High, Low, Starting_time, Ending_time, FTC, EL, MPL, weight)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE Unique_Point = Unique_Point""",
                        flag_values
                    )
                    await conn.commit()

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
        """Batch update all DP weights in a single database transaction"""
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
  
    async def _insert_positions_batch(self, positions: list[tuple[str, str, float, float, float, datetime.datetime, int, int]]):
        """
        Insert multiple positions in a batch using executemany.
        :param positions: List of tuples containing data for each position
        """
        # Validate input (we assume positions are already validated)
        if not positions:
            return

        # Prepare the SQL query
        query = f"""
            INSERT INTO {self.Positions_table_name} 
            (Traded_DP, Order_type, Price, SL, TP, Last_modified_time, Vol, Order_ID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
