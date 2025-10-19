config = AlphaConfig(start_date = '2006-01-01')
def alpha_issmanu_p1w1wl4(s: Streams):
    """
    # Hypothesis: An increase in the percentage difference between the current week's U.S. Purchasing Manager's Index level
    # and the average of the previous four weeks levels may indicate potential excess demand for base metals,
    # leading to a corresponding rise in prices, with the opposite effect applying in reverse.
    """
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_w1 = ts_mean(issmanu, window=week)
    issmanu_wl4 = ts_mean(issmanu, window=month)
    issmanu_p1w1wl4 = safe_div((issmanu_w1 - issmanu_wl4), issmanu_w1)
    issmanu_p1w1wl4_zn = zscore(issmanu_p1w1wl4, window=annual)
    return issmanu_p1w1wl4_zn