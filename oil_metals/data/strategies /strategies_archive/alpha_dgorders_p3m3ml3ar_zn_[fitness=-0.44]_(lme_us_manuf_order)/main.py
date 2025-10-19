config = AlphaConfig()
def alpha_dgorders_p3m3ml3ar_zn(s: Streams):
    """
    # Hypothesis:  An increase in durable goods orders over last 3 months, particularly for items with a production period exceeding three years,
    # indicates a revitalization of short-term economic activity in the U.S., potentially driving short-term demand growth for base metals and leading to higher prices.
    # Conversely, a decline in durable goods orders suggests the opposite effect.
    """
    dgorders = ts_ffill(s.lme_us_manuf_order)
    latest_3m = ts_mean(dgorders, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = (latest_3m - previous_3m) / previous_3m
    dgorders_p3m3ml3ar = pct_change_3m * 4
    dgorders_p3m3ml3ar_zn = zscore(dgorders_p3m3ml3ar, window=month)
    return dgorders_p3m3ml3ar_zn