config = AlphaConfig()
def alpha_issmanu_3mma_zn(s: Streams):
    """
    # Hypothesis: An increase in the Purchasing Managers' Index (PMI) over last 3 months leads to a rise in business activity,
    which in turn increases the medium-term demand for base metals and their prices. Conversely, a decrease in the PMI results in the opposite effect.
    """
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_3mma = ts_mean(issmanu, window=quarterly)
    issmanu_3mma_zn = zscore(issmanu_3mma, window=quarterly)
    return issmanu_3mma_zn