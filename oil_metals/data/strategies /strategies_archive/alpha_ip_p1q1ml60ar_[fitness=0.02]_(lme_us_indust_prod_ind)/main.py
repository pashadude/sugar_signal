config = AlphaConfig(start_date = '2006-01-01')
def alpha_ip_p1q1ml60ar(s: Streams):
    """
    "Hypothesis: A quarterly increase  (percent) in U.S. Industrial Production above the 5-year average
    may indicate excess demand for base metals, driving up prices, while a decrease suggests the opposite.
    """
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_q1 = ts_mean(ip, window=quarterly)
    ip_ml60 = ts_mean(ip, window=months_60)
    ip_p1q1ml60 = safe_div((ip_q1 - ip_ml60), ip_q1)
    ip_p1q1ml60ar = ip_p1q1ml60 * 4
    ip_q1ml60ar_zn = zscore(ip_p1q1ml60ar, window=annual)
    return ip_q1ml60ar_zn