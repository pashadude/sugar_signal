config = AlphaConfig()
def alpha_m2_delta(s:Streams):
    """
    Hypothesis: Higher change normalized money supply (M2) may indicate short-term economic stimulus from the Central Bank,
    potentially boosting demand for base metals and supporting their prices.
    """
    m2 = ts_ffill(s.lme_us_mon_sup)
    m2_diff = delta(m2, period=month_2)
    return zscore(m2_diff, window=month_2)