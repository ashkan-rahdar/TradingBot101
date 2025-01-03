import pandas as pd
from openpyxl import load_workbook
import os

def save_to_excel_realtime(dataframe, file_name, sheet_name="Flags Data"):
    try:
        if not os.path.exists(file_name):
            # If the file does not exist, create it
            with pd.ExcelWriter(file_name, engine="openpyxl", mode="w") as writer:
                dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
        else:
            # Open an existing file or replace the sheet
            with pd.ExcelWriter(file_name, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
        print(f"Updated {file_name} at {pd.Timestamp.now()}")
    except Exception as e:
        print(f"Failed to save to Excel: {e}")