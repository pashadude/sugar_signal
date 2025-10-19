config = AlphaConfig(start_date = '2006-01-01')
def alpha_issmanu_d1m1ml69(s: Streams):
    """
    Hypothesis: A positive difference between the U.S. Purchasing Mangers' Index for the last month,
    and the average of the past 69 months may indicate potential excess demand for base metals,
    leading to a rise in their prices. Conversely, a negative difference suggests the opposite effect.
    """
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_m1 = ts_mean(issmanu, window=month)
    issmanu_ml69 = ts_mean(issmanu, window=months_69)
    issmanu_p1m1ml69 = safe_div((issmanu_m1 - issmanu_ml69), issmanu_m1)
    issmanu_d1ml69ar_zn = zscore(issmanu_p1m1ml69, window=annual)
    return issmanu_d1ml69ar_zn