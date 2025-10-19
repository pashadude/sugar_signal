config = AlphaConfig()
def alpha_philmanu_d3m3ml3_zn(s: Streams):
    """
    # Hypothesis: An increase in manufacturing activity in the Philadelphia district drives higher demand for commodities in short-term period,
    # particularly leading to a rise in base metal prices. Conversely, a decrease in the index results in a decline in base metal prices.
    """
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    latest_3m = ts_mean(philmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    philmanu_d3m3ml3 = (previous_3m - latest_3m)
    philmanu_d3m3ml3_zn = zscore(philmanu_d3m3ml3, window=month)
    return philmanu_d3m3ml3_zn