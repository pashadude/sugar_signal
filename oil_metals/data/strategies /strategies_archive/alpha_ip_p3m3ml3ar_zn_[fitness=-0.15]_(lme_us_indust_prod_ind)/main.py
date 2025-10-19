config = AlphaConfig()
def alpha_ip_p3m3ml3ar_zn(s: Streams):
    """
    Hypothesis: The industrial production in the U.S. over the past three months can drive medium-term demand for base metals.
    Conversely, a decline in the industrial production index may result in reduced demand for base metals and a corresponding drop in their prices.
    """
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    latest_3m = ts_mean(ip, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = (latest_3m - previous_3m) / previous_3m
    ip_p3m3ml3ar = pct_change_3m * 4
    ip_p3m3ml3ar_zn = zscore(ip_p3m3ml3ar, window=month)
    return ip_p3m3ml3ar_zn