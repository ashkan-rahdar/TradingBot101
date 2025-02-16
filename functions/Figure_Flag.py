import pandas as pd
import plotly.express as pt
import plotly.graph_objects as go
import numpy as np

def Figure_Flag(dataset: pd.DataFrame, FLAGS: pd.DataFrame, Name):
    
    # Extract high prices and indices for Bullish and Bearish flags
    High_figure = {
        "Bullish": FLAGS[FLAGS['Type'] == 'Bullish']['High'].apply(lambda x: x.price).tolist(),
        "Bearish": FLAGS[FLAGS['Type'] == 'Bearish']['High'].apply(lambda x: x.price).tolist()
    }

    Low_figure = {
        "Bullish": FLAGS[FLAGS['Type'] == 'Bullish']['Low'].apply(lambda x: x.price).tolist(),
        "Bearish": FLAGS[FLAGS['Type'] == 'Bearish']['Low'].apply(lambda x: x.price).tolist()
    }
    Time_figure = {
        "High_Bullish": FLAGS[FLAGS['Type'] == 'Bullish']['High'].apply(lambda x: x.time).tolist(),
        "High_Bearish": FLAGS[FLAGS['Type'] == 'Bearish']['High'].apply(lambda x: x.time).tolist(),
        "Low_Bullish": FLAGS[FLAGS['Type'] == 'Bullish']['Low'].apply(lambda x: x.time).tolist(),
        "Low_Bearish": FLAGS[FLAGS['Type'] == 'Bearish']['Low'].apply(lambda x: x.time).tolist()
    }

    Important_DPs_figure = {
        "FTC_High": FLAGS['FTC'].apply(lambda x: x.DP.High.price).tolist(),
        "FTC_Lows": FLAGS['FTC'].apply(lambda x: x.DP.Low.price).tolist(),

        "EL_High": FLAGS['EL'].apply(lambda x: x.DP.High.price).tolist(),
        "EL_Lows": FLAGS['EL'].apply(lambda x: x.DP.Low.price).tolist()
    }
    Time_DPs_figure = {
        "FTC_High": FLAGS['FTC'].apply(lambda x: x.DP.High.time).tolist(),
        "FTC_Lows": FLAGS['FTC'].apply(lambda x: x.DP.Low.time).tolist(),

        "EL_High": FLAGS['EL'].apply(lambda x: x.DP.High.time).tolist(),
        "EL_Lows": FLAGS['EL'].apply(lambda x: x.DP.Low.time).tolist(),
    }

    # Generate a list of indexes
    # indexes = list(range(len(dataset['high'])))

    fig = go.Figure()

    # Add the first line (e.g., 'close' prices)
    fig.add_trace(go.Scatter(x=Time_figure['High_Bullish'], y=High_figure['Bullish'], mode='markers', name='High of Bullish Flags'))
    fig.add_trace(go.Scatter(x=Time_figure['High_Bearish'], y=High_figure['Bearish'], mode='markers', name='High of Bearish Flags'))


    fig.add_trace(go.Scatter(x=Time_figure['Low_Bullish'], y=Low_figure['Bullish'], mode='markers', name='Low of Bullish Flags'))
    fig.add_trace(go.Scatter(x=Time_figure['Low_Bearish'], y=Low_figure['Bearish'], mode='markers', name='Low of Bearish Flags'))

    fig.add_trace(go.Scatter(x=Time_DPs_figure['FTC_Lows'], y=Important_DPs_figure['FTC_Lows'], mode='markers', name='Low of FTC'))
    fig.add_trace(go.Scatter(x=Time_DPs_figure['FTC_High'], y=Important_DPs_figure['FTC_High'], mode='markers', name='High of FTC'))
    
    fig.add_trace(go.Scatter(x=Time_DPs_figure['EL_Lows'], y=Important_DPs_figure['EL_Lows'], mode='markers', name='Low of EL'))
    fig.add_trace(go.Scatter(x=Time_DPs_figure['EL_High'], y=Important_DPs_figure['EL_High'], mode='markers', name='High of EL'))
    # Add the third line (e.g., 'High' prices)
    fig.add_trace(go.Scatter(x=dataset['time'], y=dataset['high'], mode='lines', name='High Prices'))
    # Add the second line (e.g., 'Low' prices)
    fig.add_trace(go.Scatter(x=dataset['time'], y=dataset['low'], mode='lines', name='Low Prices'))

    # Customize layout if needed
    fig.update_layout(title=f"Highs and Lows on Close price {Name}",
                    xaxis_title="Time",
                    yaxis_title="Price")

    # Show the figure
    fig.show()
        