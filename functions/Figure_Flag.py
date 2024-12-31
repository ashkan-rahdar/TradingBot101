import pandas as pd
import plotly.express as pt
import plotly.graph_objects as go

def Figure_Flag(dataset: pd.DataFrame, FLAGS: pd.DataFrame):
    # Extract high prices and indices for Bullish and Bearish flags
    High_figure = {
        "Bullish": [flag.high.price for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bullish'],
        "Bearish": [flag.high.price for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bearish']
    }

    Low_figure = {
        "Bullish": [flag.low.price for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bullish'],
        "Bearish": [flag.low.price for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bearish']
    }
    Time_figure = {
        "High_Bullish": [flag.high.index for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bullish'],
        "High_Bearish": [flag.high.index for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bearish'],
        "Low_Bullish": [flag.low.index for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bullish'],
        "Low_Bearish": [flag.low.index for flag in FLAGS['Flag informations'] if flag.flag_type == 'Bearish']
    }

    Important_DPs_figure = {
        "FTC_High": [flag.FTC.DP.High.price for flag in FLAGS['Flag informations']],
        "FTC_Lows": [flag.FTC.DP.Low.price for flag in FLAGS['Flag informations']],

        "EL_High": [flag.EL.DP.High.price for flag in FLAGS['Flag informations']],
        "EL_Lows": [flag.EL.DP.Low.price for flag in FLAGS['Flag informations']]
    }
    Time_DPs_figure = {
        "FTC_High": [flag.FTC.DP.High.index for flag in FLAGS['Flag informations']],
        "FTC_Lows": [flag.FTC.DP.Low.index for flag in FLAGS['Flag informations']],

        "EL_High": [flag.EL.DP.High.index for flag in FLAGS['Flag informations']],
        "EL_Lows": [flag.EL.DP.Low.index for flag in FLAGS['Flag informations']]
    }

    # Generate a list of indexes
    indexes = list(range(len(dataset['high'])))

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
    fig.add_trace(go.Scatter(x=indexes, y=dataset['high'], mode='lines', name='High Prices'))
    # Add the second line (e.g., 'Low' prices)
    fig.add_trace(go.Scatter(x=indexes, y=dataset['low'], mode='lines', name='Low Prices'))

    # Customize layout if needed
    fig.update_layout(title="Highs and Lows on Close price",
                    xaxis_title="Time",
                    yaxis_title="Price")

    # Show the figure
    fig.show()
        