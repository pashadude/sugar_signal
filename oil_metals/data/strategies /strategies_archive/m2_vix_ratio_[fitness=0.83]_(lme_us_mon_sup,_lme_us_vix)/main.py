config = AlphaConfig()
def m2_vix_ratio(s:Streams):
    """
    Hypothesis: The Money Supply-VIX Ratio compares smoothed percentage changes in U.S. money supply (M2) and market volatility (VIX).
    A higher ratio suggests rising market stress relative to liquidity, potentially bearish for base metals,
    while a lower ratio indicates stronger liquidity support, which may be bullish.
    """
    m2_pct = ts_pct_change(ts_ffill(s.lme_us_mon_sup), periods=month)
    vix_pct = ts_pct_change(s.lme_us_vix, periods = week_2)
    m2_pct_wma = ts_ewm(m2_pct, span=month, adjust=True, min_periods=1, ignore_na=False)
    vix_pct_wma = ts_ewm(vix_pct, span=month, adjust=True, min_periods=1, ignore_na=False)
    m2_vix_ratio = safe_div(vix_pct_wma, m2_pct_wma)
    return m2_vix_ratio