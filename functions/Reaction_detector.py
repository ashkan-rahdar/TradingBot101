import pandas as pd
import typing
import os
import sys
import numpy as np
import json
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.DP_Parameteres import DP_Parameteres

with open("./config.json", "r") as file:
    config = json.load(file)

async def Reaction_to_DP(DP: DP_Parameteres, 
                   dataset: pd.DataFrame, 
                   direction: typing.Literal["Bullish", "Bearish","Undefined"],
                   start: int):
    reaction = None
    if direction == "Bullish" and DP.High.price is not None and DP.Low.price is not None and start is not None and DP.Status == "Active":
        # Find the initial index where 'low' crosses below DP.High.price
        initial_indexes = dataset.index[dataset["low"] <= DP.High.price]
        if initial_indexes.empty:
            return None
        
        initial_index = initial_indexes[0]

        # Find the close index where 'low' crosses below DP.Low.price
        close_indexes = dataset.index[initial_index + 1 - start:][dataset["low"][initial_index + 1-start:] <= DP.Low.price]
        close_index = close_indexes[0] if not close_indexes.empty else len(dataset) - 1

        # Calculate reaction
        TP = dataset["high"].iloc[initial_index - start + 1:close_index - start].max()
        reaction = (TP - DP.High.price) / (DP.High.price - DP.Low.price)
        DP.Status = "Used"

        reaction *= DP.weight
        
    elif direction == "Bearish" and DP.High.price is not None and DP.Low.price is not None and start is not None and DP.Status == "Active": 
        # Find the initial index where 'high' crosses higher DP.Low.price
        initial_indexes = dataset.index[dataset["high"] >= DP.Low.price]
        if initial_indexes.empty:
            return None
        
        initial_index = initial_indexes[0]

        # Find the close index where 'high' crosses higher DP.High.price
        close_indexes = dataset.index[initial_index + 1 -start:][dataset["high"][initial_index + 1 -start:] >= DP.High.price]
        close_index = close_indexes[0] if not close_indexes.empty else len(dataset) - 1

        # Calculate reaction
        TP = dataset["low"].iloc[initial_index -start + 1:close_index - start].min()
        reaction = (-TP + DP.Low.price) / (DP.High.price - DP.Low.price)
        DP.Status = "Used"

        reaction *= DP.weight
    return reaction

async def Reaction_detector(flags: pd.DataFrame, dataset: pd.DataFrame):
    Reaction_to_FTC = []
    Reaction_to_EL = []
    for flag in flags['Flag informations']:
        Reaction_to_EL.append(await Reaction_to_DP(flag.EL.DP, dataset.iloc[flag.EL.DP.start_index:], flag.flag_type, flag.EL.DP.start_index))
        Reaction_to_FTC.append(await Reaction_to_DP(flag.FTC.DP, dataset.iloc[flag.FTC.DP.start_index:], flag.flag_type, flag.FTC.DP.start_index)) 
    
    flags["Reaction to FTC"] = Reaction_to_FTC
    flags["Reaction to EL"] = Reaction_to_EL

async def backtest_FLAGS(FLAGS, column_name, RR_values, commision, R, account_balance):
    RESULT = []
    Winrates = []

    for RR in RR_values:
        result = 0
        Total_SLs = 0
        flag_index = -1
        trades =0

        # Iterate through reactions
        for value in FLAGS[column_name]:
            flag_index += 1
            if pd.isna(value):  # Skip NaN values
                continue

            trades += 1
            weight = FLAGS['Flag informations'][flag_index].weight
            if value <= RR:
                Total_SLs += 1
                result -= R*weight
            elif value > RR:
                result += R*RR*weight

            result -= commision

    
        winrate = 1 - (Total_SLs / trades)
        RESULT.append(result)
        Winrates.append(winrate * 100)

    # # Plot Results
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=np.array(Winrates), y=np.array(RESULT), mode='lines', name=column_name))
    # #fig.add_trace(go.Scatter(x=np.array(Winrates_bullish), y=np.array(RESULT_bullish), mode='lines', name=column_name + "bullish"))
    # #fig.add_trace(go.Scatter(x=np.array(Winrates_bearish), y=np.array(RESULT_bearish), mode='lines', name=column_name + "bearish"))
    # fig.update_layout(title=f"RESAULT {column_name}",
    #                 xaxis_title="Winrate (%)",
    #                 yaxis_title=f"RESAULT (R={R}%)")
    # fig.show()
    # # Plot Results
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=RR_values, y=np.array(RESULT) * np.array(Winrates) / 100, mode='lines', name=column_name))
    # #fig.add_trace(go.Scatter(x=RR_values, y=np.array(RESULT_bullish) * np.array(Winrates_bullish) / 100, mode='lines', name=column_name+ "bullish"))
    # #fig.add_trace(go.Scatter(x=RR_values, y=np.array(RESULT_bearish) * np.array(Winrates_bearish) / 100, mode='lines', name=column_name+ "bearish"))
    # fig.update_layout(title=f"WinRate * RESULT vs RR in {column_name}",
    #                 xaxis_title="RR",
    #                 yaxis_title="WinRate * RESULT")
    # fig.show()

    # Plot Results
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=RR_values, y=100*np.array(RESULT)/account_balance, mode='lines', name="Profit"))
    fig.add_trace(go.Scatter(x=RR_values, y=np.array(Winrates), mode='lines', name="Winrate"))
    #fig.add_trace(go.Scatter(x=RR_values, y=np.array(RESULT_bullish), mode='lines', name=column_name+ "bullish"))
    #fig.add_trace(go.Scatter(x=RR_values, y=np.array(RESULT_bearish), mode='lines', name=column_name+ "bearish"))
    fig.update_layout(title=column_name,
                    xaxis_title="RR",
                    yaxis_title="Percentage")
    fig.show()

    # Identify valid RRs
    valid_RRs = RR_values[(np.array(RESULT) == np.array(RESULT).max())]
    print(f"Valid RRs based on {column_name}: {valid_RRs}")

    print (f"total number of trades:{trades}")
    return np.array(RESULT), np.array(Winrates)
    

async def main_reaction_detector(FLAGS: pd.DataFrame, DataSet: pd.DataFrame, account_balance: int):
    await Reaction_detector(FLAGS,DataSet)

    # Constants
    R = (config["trading_configs"]["risk_management"]["R"] /100 ) * account_balance
    commision = config["account_info"]["commision"]
    RR_values = np.arange(0.1, 10, 0.01)

    # Calculate metrics
    Profits_EL, Winrates_EL = await backtest_FLAGS(FLAGS, 'Reaction to EL', RR_values, commision, R, account_balance)
    Profits_FTC, Winrates_FTC = await backtest_FLAGS(FLAGS, 'Reaction to FTC', RR_values, commision, R, account_balance)