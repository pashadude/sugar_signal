config = AlphaConfig(start_date = '2006-01-01')
def alpha_dgorders_p1w1wl4(s: Streams):
    """
    Hypothesis: An increase in the percentage difference between the current week's Durable Goods production
    and the average of the previous four weeks levels may indicate potential excess demand for base metals,
    leading to a corresponding rise in prices, with the opposite effect applying in reverse.
    """
    dgorders = ts_ffill(s.lme_us_manuf_order)
    dgorders_w1 = ts_mean(dgorders, window=week)
    dgorders_wl4 = ts_mean(dgorders, window=month)
    dgorders_p1w1wl4 = safe_div((dgorders_w1 - dgorders_wl4), dgorders_w1)
    dgorders_p1w1wl4_zn = zscore(dgorders_p1w1wl4, window=annual)
    return dgorders_p1w1wl4_zn