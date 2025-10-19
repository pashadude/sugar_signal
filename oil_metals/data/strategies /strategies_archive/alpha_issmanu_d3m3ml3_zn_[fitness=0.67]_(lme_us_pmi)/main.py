config = AlphaConfig()
def alpha_issmanu_d3m3ml3_zn(s: Streams):
    """
    # Hypothesis: An increase in the Purchasing Managers' Index (PMI) over last 3 months leads to a rise in business activity,
    # which in turn increases the short-term demand for base metals and their prices.
    # Conversely, a decrease in the PMI results in the opposite effect.
    """
    ismmanu = ts_ffill(s.lme_us_pmi)
    latest_3m = ts_mean(ismmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    issmanu_d3m3ml3 = (previous_3m - latest_3m)
    issmanu_d3m3ml3_zn = zscore(issmanu_d3m3ml3, window=month)
    return issmanu_d3m3ml3_zn