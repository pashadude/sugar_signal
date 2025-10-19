config = AlphaConfig(start_date = '2006-01-01')
def alpha_issmanu_p1q1ml60ar(s: Streams):
    """
    Hypothesis: A quarterly increase (percent) in U.S. Producers Managers' Index level above the 5-year average
    may indicate excess demand for base metals, driving up prices, while a decrease suggests the opposite.
    """
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_q1 = ts_mean(issmanu, window=quarterly)
    issmanu_ml60 = ts_mean(issmanu, window=months_60)
    issmanu_p1q1ml60 = safe_div((issmanu_q1 - issmanu_ml60), issmanu_q1)
    issmanu_p1q1ml60ar = issmanu_p1q1ml60 * 4
    issmanu_q1ml60ar_zn = zscore(issmanu_p1q1ml60ar, window=annual)
    return issmanu_q1ml60ar_zn