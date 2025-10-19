config = AlphaConfig(start_date = '2006-01-01')
def alpha_dgorders_d1w1wl4(s: Streams):
    """
    Hypothesis: An increase in the Durable Goods production over the past four weeks may signal
    a corresponding rise in base metal demand, potentially leading to higher prices, and vice versa.
    """
    dgorders = ts_ffill(s.lme_us_manuf_order)
    dgorders_w1 = ts_mean(dgorders, window=week)
    dgorders_wl4 = ts_mean(dgorders, window=month)
    dgorders_d1w1wl4 = dgorders_w1 - dgorders_wl4
    dgorders_d1w1wl4_zn = zscore(dgorders_d1w1wl4, window=annual)
    return dgorders_d1w1wl4_zn