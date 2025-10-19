config = AlphaConfig()
def alpha_philmanu_3mma_zn(s: Streams):
    """
    # Hypothesis: An increase in manufacturing activity in the Philadelphia district drives higher demand for commodities in medium-term period,
    # particularly leading to a rise in base metal prices. Conversely, a decrease in the index results in a decline in base metal prices.
    """
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    philmanu_3mma = ts_mean(philmanu, window=quarterly)
    philmanu_3mma_zn = zscore(philmanu_3mma, window=quarterly)
    return philmanu_3mma_zn