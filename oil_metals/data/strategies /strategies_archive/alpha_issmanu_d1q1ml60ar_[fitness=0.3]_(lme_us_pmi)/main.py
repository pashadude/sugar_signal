config = AlphaConfig(start_date = '2006-01-01')
def alpha_issmanu_d1q1ml60ar(s: Streams):
    """
    Hypothesis: A rise in the quarterly U.S. Producers Managers' Index relative to its 5-year average
    may indicate excess demand for base metals, leading to higher prices, while a decline suggests the opposite.
    """
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_q1 = ts_mean(issmanu, window=quarterly)
    issmanu_ml60 = ts_mean(issmanu, window=months_60)
    issmanu_d1q1ml60 = issmanu_q1 - issmanu_ml60
    issmanu_d1q1ml60ar = issmanu_d1q1ml60 * 4
    issmanu_d1ml60ar_zn = zscore(issmanu_d1q1ml60ar, window=annual)
    return issmanu_d1ml60ar_zn