config = AlphaConfig(start_date = '2006-01-01')
def alpha_philmanu_d1w1wl4(s: Streams):
    """
    Hypothesis: An increase in the Manufacturing Production in Philadelphia district over the past four weeks
    may signal a corresponding rise in base metal demand, potentially leading to higher prices, and vice versa.
    """
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    philmanu_w1 = ts_mean(philmanu, window=week)
    philmanu_wl4 = ts_mean(philmanu, window=month)
    philmanu_d1w1wl4 = philmanu_w1 - philmanu_wl4
    philmanu_d1w1wl4_zn = zscore(philmanu_d1w1wl4, window=annual)
    return philmanu_d1w1wl4_zn