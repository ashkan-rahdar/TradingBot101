import sys
import os
import math
import json


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Metatrader_Module import CMetatrader_Module

with open("./config.json", "r") as file:
    config = json.load(file)
    
TARGET_PROB = config["trading_configs"]["risk_management"]["MIN_Prob"]
DD_Daily: float = config["trading_configs"]["risk_management"]["DD_Monthly"]/30
Max_No_Trade_Daily: int = config["trading_configs"]["risk_management"]["Max_No_Trade_Daily"]

class Position_Manager_Class:
    
    @staticmethod
    def Vol_Calculator_RiskBased_Function(entry_price: float, stop_loss_price: float, risk_percent: float, symbol: str) -> float:
        account_info = CMetatrader_Module.mt.account_info() # type: ignore
        if account_info is None:
            raise Exception("Failed to fetch account info.")

        balance = account_info.balance
        risk_amount = (risk_percent / 100) * balance

        symbol_info = CMetatrader_Module.mt.symbol_info(symbol) # type: ignore
        if symbol_info is None:
            raise Exception(f"Symbol {symbol} not found.")

        tick_size = symbol_info.trade_tick_size
        tick_value = symbol_info.trade_tick_value
        volume_min = symbol_info.volume_min
        volume_max = symbol_info.volume_max
        volume_step = symbol_info.volume_step

        if tick_size == 0 or tick_value == 0:
            raise Exception(f"Invalid tick size or tick value for {symbol}.")

        # === Calculate loss per lot dynamically ===
        sl_distance_in_price = abs(entry_price - stop_loss_price)
        if sl_distance_in_price == 0:
            raise Exception("Stop Loss distance cannot be zero.")

        # loss for 1 lot
        loss_per_lot = (sl_distance_in_price / tick_size) * tick_value

        if loss_per_lot == 0:
            raise Exception("Loss per lot is zero, cannot divide.")

        # === Calculate the volume ===
        volume = risk_amount / loss_per_lot

        # === Round properly ===
        volume = max(volume_min, min(volume_max, round(volume / volume_step) * volume_step))
        return volume
    
    @staticmethod
    def Risk_Calculator_Function(
        Trade_RR: float,
        Estimated_Trade_win_Prob: float,
        Estimated_trade_nums_Daily: int = Max_No_Trade_Daily,
        Daily_Max_Drawdown: float = DD_Daily,
        Confidence_Coefficient : float = 0.98,  # e.g., 0.95 for 95% confidence
        Kelly_Scale: float = 0.1,
    ) -> float:
        """
        Estimate optimal per-trade risk to keep drawdown within limits,
        using:
            - losing streak modeling (log-stable)
            - Kelly criterion (with capped risk)
            - confidence scaling (model reliability)

        Returns the lower of:
            - Max acceptable drawdown divided by worst-case losing streak
            - Kelly-based optimal risk scaled by safety factor
        """

        # Check inputs
        if Estimated_trade_nums_Daily < 1:
            return 0.0
        if Estimated_Trade_win_Prob <= TARGET_PROB or Estimated_Trade_win_Prob >= 1.0:
            return 0.0

        # Convert confidence level to alpha (probability of hitting or exceeding the streak)
        alpha = 1.0 - Confidence_Coefficient
        Max_Kelly_Risk: float = min(0.005 * Estimated_trade_nums_Daily, 0.0125)

        # Binary search for worst-case losing streak length that respects confidence level
        low, high = 1, Estimated_trade_nums_Daily
        while low < high:
            mid = (low + high) // 2
            # Log-safe computation of streak probability
            try:
                inner = math.pow(1 - Estimated_Trade_win_Prob, mid)
                log_prob = (Estimated_trade_nums_Daily - mid + 1) * math.log1p(-inner)
                streak_prob = 1 - math.exp(log_prob)
            except (ValueError, OverflowError):
                streak_prob = 1.0  # Assume failure if math breaks

            if streak_prob <= alpha:
                high = mid
            else:
                low = mid + 1

        losing_streak_length = low
        Losing_streak_risk = Daily_Max_Drawdown / losing_streak_length

        # Kelly fraction calculation
        p = Estimated_Trade_win_Prob
        q = 1.0 - p
        mu = p * Trade_RR - q * 1.0
        sigma2 = p * (Trade_RR - mu) ** 2 + q * (-1.0 - mu) ** 2
        if sigma2 == 0.0:
            kelly_fraction = 0.0
        else:
            kelly_fraction = mu / sigma2

        # Scale Kelly fraction to prevent over-risking
        kelly_fraction_risk = max(0.0, min(Kelly_Scale * kelly_fraction, Max_Kelly_Risk))
        
        return min(kelly_fraction_risk, Losing_streak_risk)
    
    
    @staticmethod
    def model_score_Function(winrate: float, pnl_percent: float, num_trades: int,
                winrate_weight: float = 0.4, PNL_weight: float = 0.6, num_trades_weight: float = 50) -> float:
        if num_trades == 0:
            return -1  # Invalid model

        pnl_per_trade = pnl_percent / num_trades
        confidence_penalty = 1 - math.exp(-num_trades / num_trades_weight)

        score = (winrate * winrate_weight) + ((pnl_per_trade / (DD_Daily/Max_No_Trade_Daily) )* PNL_weight) * confidence_penalty
        return score