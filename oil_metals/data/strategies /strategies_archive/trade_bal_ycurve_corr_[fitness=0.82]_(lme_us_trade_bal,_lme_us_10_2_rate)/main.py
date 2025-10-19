config = AlphaConfig()
def trade_bal_ycurve_corr(s:Streams):
    """
    Hypothesis: The correlation between U.S. trade balance growth and the yield curve measures economic conditions.
    A negative correlation suggests rising recession risks, potentially weakening base metal demand and prices.
    """
    trade_bal_pct = ts_pct_change(ts_ffill(s.lme_us_trade_bal), periods=month)
    trade_bal_pct_3mma = ts_mean(trade_bal_pct, window=quarterly)
    trade_bal_pct_3mma_zn  = zscore(trade_bal_pct_3mma, window=month)
    ycurve_pct = ts_pct_change(s.lme_us_10_2_rate, periods=week)
    ycurve_pct_3mma = ts_mean(ycurve_pct, window=quarterly)
    ycurve_pct_3mma_zn = zscore(ycurve_pct_3mma, window=week_3)
    trade_balance_ycurve_corr = correlation(trade_bal_pct_3mma_zn, ycurve_pct_3mma_zn)
    return - trade_balance_ycurve_corr