config = AlphaConfig()
def alpha_ip_p1m1ml12_3mma_zn(s: Streams):
    """
    Hypothesis: The industrial production in the U.S. over last year can drive medium-term demand for base metals.
    Conversely, a decline in the industrial production index may result in reduced demand for base metals and a corresponding drop in their prices.
    """
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_pct_change = ts_pct_change(ip, periods=annual)
    ip_p1m1ml12_3mma = ts_mean(ip_pct_change, window=quarterly)
    ip_p1m1ml12_3mma_zn = zscore(ip_p1m1ml12_3mma, window=quarterly)
    return ip_p1m1ml12_3mma_zn