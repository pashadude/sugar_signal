config = AlphaConfig(start_date = '2006-01-01')
def alpha_issmanu_p1m1ml60(s: Streams):
    """
    Hypothesis: A positive percentage difference between the U.S. Purchasing Managers' Index for the last month,
    and the average of the past 5 years may indicate potential excess demand for base metals,
    leading to a rise in their prices. Conversely, a negative difference suggests the opposite effect.
    """
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_m1 = ts_mean(issmanu, window=month)
    issmanu_ml60 = ts_mean(issmanu, window=months_60)
    issmanu_p1m1ml60 = safe_div((issmanu_m1 - issmanu_ml60), issmanu_m1)
    issmanu_d1ml60ar_zn = zscore(issmanu_p1m1ml60, window=annual)
    return issmanu_d1ml60ar_zn