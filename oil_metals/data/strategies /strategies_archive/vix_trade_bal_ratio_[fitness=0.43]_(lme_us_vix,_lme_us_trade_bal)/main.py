config = AlphaConfig()
def vix_trade_bal_ratio(s:Streams):
    """
    Hypothesis: The Trade Balance to VIX Ratio compares the smoothed changes in U.S. trade balance and market volatility (VIX).
    A higher ratio (more negative signal) suggests rising market uncertainty relative to trade balance improvements,
    potentially indicating risk-off sentiment and weaker base metal prices.
    """
    vix_diff = delta(s.lme_us_vix, period=week_2)
    trade_bal_diff = ts_delay(delta(ts_ffill(s.lme_us_trade_bal), period=month), period=month_2)
    vix_diff_wma2 = ts_mean(ts_ewm(vix_diff, span=month, adjust=True, min_periods=1, ignore_na=False), window=week_2)
    trade_bal_diff_wma2 = ts_mean(ts_ewm(trade_bal_diff, span=month, adjust=True, min_periods=1, ignore_na=False), window=month_2)
    vix_trade_bal_ratio = zscore(safe_div(vix_diff_wma2, trade_bal_diff_wma2), window=month_2)
    return - vix_trade_bal_ratio