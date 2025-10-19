config = AlphaConfig()
def alpha_trade_balance_mom_zn(s:Streams):
    """
    Hypothesis: The signal tracks U.S. Treasury liquidity shifts via short- and medium-term balance changes.
    Increased liquidity may boost base metal demand, while tightening signals weaker prices.
    """
    trade_bal = ts_ffill(s.lme_us_tres_bal)
    trade_bal_perc = ts_pct_change(trade_bal, periods=month)
    trade_bal_perc_3mma = ts_mean(trade_bal_perc, window=quarterly)
    trade_bal_perc_6mma = ts_mean(trade_bal_perc, window=half)
    trade_bal_perc_diff = trade_bal_perc_3mma - trade_bal_perc_6mma
    trade_bal_zn = zscore(trade_bal_perc_diff, window=half)
    return trade_bal_zn