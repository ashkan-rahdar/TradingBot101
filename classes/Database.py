import mysql.connector
import pandas as pd
import sys
import os
from colorama import Fore,Style
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag_Class
from functions.logger import print_and_logging_Function
from classes.FlagPoint import FlagPoint_Class
from classes.DP_Parameteres import DP_Parameteres_Class

class Database_Class:
    def __init__(self, The_timeframe: str):

        self.flag_points_table_name = f"Flag_Points_{The_timeframe}"
        self.important_dps_table_name = f"Important_DPs_{The_timeframe}"
        self.flags_table_name = f"Flags_{The_timeframe}"
        self.Positions_table_name = f"Positions_{The_timeframe}"

        self.TimeFrame = The_timeframe
        print_and_logging_Function("info", f"The DataBase of {The_timeframe} is initializing...", "description")
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="TradingBot",
                password="Nama-123456",
                database="tradingbotdb",
                connection_timeout=10
            )
            self.cursor = self.db.cursor()
            self._initialize_tables_Function()
            self.Traded_DP_Set = set()
        except Exception as e:
            print_and_logging_Function("error", f"An error occured in initialization of DB connection: {e}", "title")

    def _initialize_tables_Function(self):
        queries = [
            f"""
            CREATE TABLE IF NOT EXISTS {self.flag_points_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                price FLOAT NULL,
                time DATETIME NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.important_dps_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type ENUM('FTC', 'EL', 'MPL') NULL,
                High_Point INT NULL,
                Low_Point INT NULL,
                weight FLOAT NULL,
                first_valid_trade_time DATETIME NOT NULL,
                trade_direction ENUM('Bullish', 'Bearish', 'Undefined') NULL,
                FOREIGN KEY (High_Point) REFERENCES {self.flag_points_table_name}(id) ON DELETE SET NULL,
                FOREIGN KEY (Low_Point) REFERENCES {self.flag_points_table_name}(id) ON DELETE SET NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.flags_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Unique_Point DATETIME NOT NULL,
                type ENUM('Bullish', 'Bearish', 'Undefined') NOT NULL,
                High INT NOT NULL,
                Low INT NOT NULL,
                Starting_time DATETIME NOT NULL,
                Ending_time DATETIME NOT NULL,
                FTC INT,
                EL INT,
                MPL INT,
                weight FLOAT NOT NULL,
                FOREIGN KEY (High) REFERENCES {self.flag_points_table_name}(id),
                FOREIGN KEY (Low) REFERENCES {self.flag_points_table_name}(id),
                FOREIGN KEY (FTC) REFERENCES {self.important_dps_table_name}(id) ON DELETE SET NULL,
                FOREIGN KEY (EL) REFERENCES {self.important_dps_table_name}(id) ON DELETE SET NULL,
                FOREIGN KEY (MPL) REFERENCES {self.important_dps_table_name}(id) ON DELETE SET NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.Positions_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Traded_DP INT,
                Order_type ENUM('Buy', 'Sell', 'Buy Limit', 'Sell Limit') NOT NULL,
                Price FLOAT NOT NULL,
                SL FLOAT NOT NULL,
                TP FLOAT NOT NULL,
                Last_modified_time DATETIME NOT NULL,
                Vol FLOAT Not Null,
                Order_ID INT Not Null,
                Result INT NOT Null DEFAULT 0,
                FOREIGN KEY (Traded_DP) REFERENCES {self.important_dps_table_name}(id) ON DELETE SET NULL
            )
            """
        ]
        
        try:
            for query in queries:
                self.cursor.execute(query)
            self.db.commit()
            print_and_logging_Function("info", f"{self.TimeFrame} Tables of created successfully!", "title")
        except Exception as e:
            print_and_logging_Function("error", f"Couldn't initialize DB: {e}", "title")

    async def save_data_Function(self, The_flag: Flag_Class):
        high_id = self._insert_flag_point_Function(The_flag.high)
        low_id = self._insert_flag_point_Function(The_flag.low)
        ftc_id = self._insert_important_dp_Function(The_flag.FTC) if The_flag.FTC else None
        el_id = self._insert_important_dp_Function(The_flag.EL) if The_flag.EL else None
        mpl_id = self._insert_important_dp_Function(The_flag.MPL) if The_flag.MPL else None
        
        self.cursor.execute(
            f"""INSERT INTO {self.flags_table_name} (Unique_Point, type, High, Low, Starting_time, Ending_time, FTC, EL, MPL, weight)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (The_flag.Unique_point, The_flag.flag_type, high_id, low_id, The_flag.Start_time, The_flag.End_time, ftc_id, el_id, mpl_id, The_flag.weight)
        )
        self.db.commit()

    def _insert_flag_point_Function(self, The_point: FlagPoint_Class) -> int:
        # Check if price or time is None
        if The_point.price is None or The_point.time is None:
            return None  # Return None for invalid points

        # Format the time to ensure consistent string representation
        formatted_time = The_point.time.strftime('%Y-%m-%d %H:%M:%S')
        
        # First, let's try to find any matching records with extremely precise comparison
        self.cursor.execute(f""" SELECT id FROM {self.flag_points_table_name} WHERE ABS(price - %s) < 0.0000001 AND time = %s""", 
                            (The_point.price, formatted_time))
        existing_row = self.cursor.fetchone()
        
        if existing_row:
            return existing_row[0]  # Return the existing row ID
        
        # If not exists, insert the new flag_point
        self.cursor.execute(
            f"INSERT INTO {self.flag_points_table_name} (price, time) VALUES (%s, %s)", 
            (The_point.price, formatted_time)
        )
        
        # Make sure to commit the transaction
        self.db.commit()
        return self.cursor.lastrowid  # Return the newly inserted row's ID

    def _insert_important_dp_Function(self, The_Important_dp: DP_Parameteres_Class) -> int:
        first_id = self._insert_flag_point_Function(The_Important_dp.High)
        second_id = self._insert_flag_point_Function(The_Important_dp.Low)

        if first_id is None or second_id is None:
            return None  # Skip insertion
        
        self.cursor.execute(
            f"""INSERT INTO {self.important_dps_table_name} (type, High_Point, Low_Point, weight, first_valid_trade_time, trade_direction)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (The_Important_dp.type , first_id, second_id, The_Important_dp.weight, The_Important_dp.first_valid_trade_time, The_Important_dp.trade_direction)
        )
        self.db.commit()
        return self.cursor.lastrowid

    def _update_dp_weights_Function(self, dps_to_update: list):
        """Batch update all DP weights in a single database transaction"""
        try:
            # Prepare the SQL query
            placeholders = ",".join(["%s"] * len(dps_to_update))
            values = [(weight, dp_id) for dp_id, weight in dps_to_update]
            
            # Execute the update
            self.cursor.executemany(
                f"UPDATE {self.important_dps_table_name} SET weight = %s WHERE id = %s", 
                values
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print_and_logging_Function("error", f"Error in batch updating DP weights: {e}", "title")
    
    def _get_tradeable_DPs_Function(self) -> list[tuple[DP_Parameteres_Class, int]]:
        # Get all important DPs in one query
        self.cursor.execute(f"SELECT id, type, High_Point, Low_Point, weight, first_valid_trade_time, trade_direction FROM {self.important_dps_table_name} WHERE weight > 0")
        dp_results = self.cursor.fetchall()
        
        # Get all flag points in one query
        flag_ids = [row[2] for row in dp_results if not pd.isna(row[2])] + [row[3] for row in dp_results if not pd.isna(row[3])]
        if flag_ids:
            self.cursor.execute(f"SELECT id, price, time FROM {self.flag_points_table_name} WHERE id IN ({','.join(['%s'] * len(flag_ids))})", flag_ids)
            flag_points = {row[0]: FlagPoint_Class(price=row[1], time=row[2]) for row in self.cursor.fetchall()}
        else:
            flag_points = {}
        
        # Build DP objects
        dps = []
        for row in dp_results:
            dp_id, dp_type, high_id, low_id, weight, first_valid_time, trade_direction = row
            high_point = flag_points.get(high_id) if not pd.isna(high_id) else None
            low_point = flag_points.get(low_id) if not pd.isna(low_id) else None
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
    
    def _insert_position(self, traded_dp_id: int, mt_order_type: str, price: float, sl: float, tp: float, 
                        Last_modified_time: datetime, vol: int, order_id: int, 
                        order_type_mapping: dict[int, str] = {0: "Buy", 1: "Sell", 2: "Buy Limit", 3: "Sell Limit"}):
        # Validate input
        if traded_dp_id is None or price is None or sl is None or tp is None or Last_modified_time is None or vol is None or order_id is None:
            raise Exception("Invalid input: traded_dp_id, price, sl, tp, Last_modified_time, vol, order_id")
            return
        
        order_type = order_type_mapping.get(mt_order_type,None)

        if order_type not in ['Buy', 'Sell', 'Buy Limit', 'Sell Limit']:
            raise Exception("Invalid Order Type")
            return

        # Format time to ensure consistent representation
        formatted_time = Last_modified_time.strftime('%Y-%m-%d %H:%M:%S')

        # Insert the position into the database
        self.cursor.execute(
            f"""INSERT INTO {self.Positions_table_name} 
                (Traded_DP, Order_type, Price, SL, TP, Last_modified_time, Vol, Order_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (traded_dp_id, order_type, price, sl, tp, formatted_time, vol, order_id)
        )

        # Commit transaction
        self.db.commit()
        
        self.Traded_DP_Set.add(traded_dp_id)
        return
