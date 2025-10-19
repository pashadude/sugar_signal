config = AlphaConfig(start_date = '2006-01-01')
def alpha_ip_d1q1ml60ar(s: Streams):
    """
    Hypothesis: A rise in the quarterly U.S. Industrial Production Index relative to its 5-year average
    may indicate excess demand for base metals, leading to higher prices, while a decline suggests the opposite.
    """
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_q1 = ts_mean(ip, window=quarterly)
    ip_ml60 = ts_mean(ip, window=months_60)
    ip_d1q1ml60 = ip_q1 - ip_ml60
    ip_d1q1ml60ar = ip_d1q1ml60 * 4
    ip_d1ml60ar_zn = zscore(ip_d1q1ml60ar, window=annual)
    return ip_d1ml60ar_zn