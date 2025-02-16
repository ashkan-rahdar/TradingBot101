import mysql.connector
import pandas as pd
import sys
import os
from colorama import Fore,Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Flag import Flag
from functions.logger import logger
from classes.FlagPoint import FlagPoint
from classes.Important_DPs import Important_DPs

class Database:
    def __init__(self, The_timeframe: str):
        self.flag_points_table_name = f"Flag_Points_{The_timeframe}"
        self.important_dps_table_name = f"Important_DPs_{The_timeframe}"
        self.flags_table_name = f"Flags_{The_timeframe}"

        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="TradingBot",
                password="Nama-123456",
                database="tradingbotdb",
                connection_timeout=10
            )
            self.cursor = self.db.cursor()
            self._initialize_tables()
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"An error occured in initialization of DB connection: {e}" + Style.RESET_ALL)
            logger.error(f"An error occured in initialization of DB connection: {e}")

    def _initialize_tables(self):
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
                First_Point INT NULL,
                Second_Point INT NULL,
                weight FLOAT NULL,
                FOREIGN KEY (First_Point) REFERENCES {self.flag_points_table_name}(id) ON DELETE SET NULL,
                FOREIGN KEY (Second_Point) REFERENCES {self.flag_points_table_name}(id) ON DELETE SET NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.flags_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
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
            """
        ]
        
        try:
            for query in queries:
                self.cursor.execute(query)
            self.db.commit()
            print(Fore.GREEN + Style.BRIGHT + f"///// Database tables based on '{self.flags_table_name}' created successfully! ////" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Couldn't initialize DB for timeframe '{self.flags_table_name}': {e}" + Style.RESET_ALL)
            logger.critical(f"Couldn't initialize DB: {e}")

    async def save_data(self, flag: Flag):
        high_id = self._insert_flag_point(flag.high)
        low_id = self._insert_flag_point(flag.low)
        ftc_id = self._insert_important_dp(flag.FTC) if flag.FTC else None
        el_id = self._insert_important_dp(flag.EL) if flag.EL else None
        mpl_id = self._insert_important_dp(flag.EL) if flag.EL else None
        
        self.cursor.execute(
            f"""INSERT INTO {self.flags_table_name} (type, High, Low, Starting_time, Ending_time, FTC, EL, MPL, weight)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (flag.flag_type, high_id, low_id, flag.Start_time, flag.End_time, ftc_id, el_id, mpl_id, flag.weight)
        )
        self.db.commit()

    def _insert_flag_point(self, point: FlagPoint) -> int:
        # Check if price or time is None
        if point.price is None or point.time is None:
            return None  # Return None for invalid points

        # Proceed with inserting into the database
        self.cursor.execute(
            f"INSERT INTO {self.flag_points_table_name} (price, time) VALUES (%s, %s)", 
            (point.price, point.time)
        )
        self.db.commit()
        return self.cursor.lastrowid  # Return the inserted row's ID


    def _insert_important_dp(self, The_Important_dp: Important_DPs) -> int:
        first_id = self._insert_flag_point(The_Important_dp.DP.High)
        second_id = self._insert_flag_point(The_Important_dp.DP.Low)

        if first_id is None or second_id is None:
            return None  # Skip insertion
        
        self.cursor.execute(
            f"""INSERT INTO {self.important_dps_table_name} (type, First_Point, Second_Point, weight)
            VALUES (%s, %s, %s, %s)""",
            (The_Important_dp.DP.type , first_id, second_id, The_Important_dp.DP.weight)
        )
        self.db.commit()
        return self.cursor.lastrowid

    def load_data(self) -> pd.DataFrame:
        self.cursor.execute(f"SELECT * FROM {self.flags_table_name}")
        flags = self.cursor.fetchall()
        columns = ["id", "Type", "High", "Low", "Starting_time", "Ending_time", "FTC", "EL", "MPL", "Weight"]
        df = pd.DataFrame(flags, columns=columns)
        df['High'] = df['High'].apply(self._get_flag_point)
        df['Low'] = df['Low'].apply(self._get_flag_point)
        df['FTC'] = df['FTC'].apply(self._get_important_dp)
        df['EL'] = df['EL'].apply(self._get_important_dp)
        df['MPL'] = df['MPL'].apply(self._get_important_dp)
        return df

    def _get_flag_point(self, flag_id: int) -> FlagPoint:
        if pd.isna(flag_id): return None
        self.cursor.execute(f"SELECT price, time FROM {self.flag_points_table_name} WHERE id = %s", (flag_id,))
        result = self.cursor.fetchone()
        return FlagPoint(price=result[0], time=result[1])

    def _get_important_dp(self, dp_id: int) -> Important_DPs:
        if pd.isna(dp_id): return None
        self.cursor.execute(f"SELECT type, First_Point, Second_Point, weight FROM {self.important_dps_table_name} WHERE id = %s", (dp_id,))
        result = self.cursor.fetchone()
        first_point = self._get_flag_point(result[1])
        second_point = self._get_flag_point(result[2])
        return Important_DPs(type=result[0], first_point=first_point, second_point=second_point, weight=result[3])
    
# MySQL_DB = Database()