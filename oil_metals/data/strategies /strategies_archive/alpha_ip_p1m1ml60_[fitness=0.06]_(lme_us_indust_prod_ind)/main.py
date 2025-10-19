config = AlphaConfig(start_date = '2006-01-01')
def alpha_ip_p1m1ml60(s: Streams):
    """
    Hypothesis: A positive percentage difference between the U.S. Industrial Production Index for the last month
    and the average of the past 5 years may indicate potential excess demand for base metals,
    leading to a rise in their prices. Conversely, a negative difference suggests the opposite effect.
    """
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_m1 = ts_mean(ip, window=month)
    ip_ml60 = ts_mean(ip, window=months_60)
    ip_p1m1ml60 = safe_div((ip_m1 - ip_ml60), ip_m1)
    ip_d1ml60ar_zn = zscore(ip_p1m1ml60, window=annual)
    return ip_d1ml60ar_zn