config = AlphaConfig()
def m2_deposit_ratio_change(s:Streams):
    """
    Hypothesis: The M2-to-Deposits Ratio Change measures the shift in U.S. money supply growth relative to deposit institution growth.
    Rising values may signal increased liquidity, potentially supporting higher base metal prices.
    """
    m2_pct = ts_pct_change(ts_ffill(s.lme_us_mon_sup), periods=month)
    dep_instit_pct = ts_pct_change(ts_ffill(s.lme_us_dep_instit), periods=week)
    m2_deposit_ratio_zn = zscore(safe_div(m2_pct, dep_instit_pct), window=month_2)
    m2_deposit_ratio_zn_change = delta(m2_deposit_ratio_zn, period=month)
    return m2_deposit_ratio_zn_change