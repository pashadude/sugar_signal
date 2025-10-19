config = AlphaConfig()
def alpha_us_10_2_delta(s: Streams):
    """
    Hypothesis: A negative yield curve difference (10-year Treasury yield minus 2-year Treasury yield)
    may serve as a leading indicator of a potential recession, signaling declining production and reduced demand
    for commodities, including base metals, resulting in lower prices.
    """
    us_10_2_rate = s.lme_us_10_2_rate
    us_10_2_rate_ma42 = ts_mean(us_10_2_rate, window=month)
    us_10_2_rate_ma63 = delta(us_10_2_rate_ma42, period=week_2)
    us_rate_delta_zn = zscore((us_10_2_rate_ma63 - us_10_2_rate_ma42), window=week_2)
    return - us_rate_delta_zn