config = AlphaConfig()
def alpha_dgorders_p1maml12_3mma_zn(s: Streams):
    """
    Hypothesis: An increase in durable goods orders from last year, particularly for items with a production period exceeding three years,
    indicates a revitalization of long-term economic activity in the U.S., potentially driving medium-term demand growth for base metals and leading to higher prices.
    Conversely, a decline in durable goods orders suggests the opposite effect.
    """
    dgorders = ts_ffill(s.lme_us_manuf_order)
    dgorders_pct_change = ts_pct_change(dgorders, periods=annual)
    dgorders_p1maml12_3mma = ts_mean(dgorders_pct_change, window=quarterly)
    dgorders_p1maml12_3mma_zn = zscore(dgorders_p1maml12_3mma, window=quarterly)
    return dgorders_p1maml12_3mma_zn