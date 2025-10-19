config = AlphaConfig()
def m2_ycurve_corr(s:Streams):
    """
    Hypothesis: The Trade Balance-Yield Curve Correlation measures the relationship between U.S. money supply changes and yield curve shifts.
    A stronger correlation may signal liquidity shifts impacting base metal demand.
    """
    m2_pct_zn  = zscore(ts_delay(ts_pct_change(ts_ffill(s.lme_us_mon_sup), periods=month), period=month_2), window=month)
    ycurve_pct_zn = zscore(ts_pct_change(s.lme_us_10_2_rate, periods=week), window=month)
    trade_balance_ycurve_corr = correlation(m2_pct_zn, ycurve_pct_zn, window=week_3)
    return trade_balance_ycurve_corr