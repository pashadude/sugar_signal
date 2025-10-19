config = AlphaConfig()
def trade_bal_close_corr(s:Streams):
    """
    Hypothesis: The Trade Balance-Price Correlation measures the relationship between U.S. trade balance shifts and base metal price changes.
    A negative correlation may signal weaker demand, pressuring metal prices.
    """
    trade_bal_ptc_zn = zscore(ts_mean(ts_delay(ts_pct_change(ts_ffill(s.lme_us_trade_bal), periods=month), period=month), window=quarterly), window=month)
    close_ptc_zn = zscore(ts_mean(ts_pct_change(s.lme_close_price, periods=week), window=week), window=month)
    trade_bal_close_corr = correlation(trade_bal_ptc_zn, close_ptc_zn, window=month_2)
    return - trade_bal_close_corr