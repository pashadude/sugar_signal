config = AlphaConfig(start_date = '2006-01-01')
def alpha_philmanu_d1m1ml69(s: Streams):
    """
    Hypothesis: A positive difference between the Philadelphia Manufacturing Index for the last month
    and the average of the past 69 months may indicate potential excess demand for base metals,
    leading to a rise in their prices. Conversely, a negative difference suggests the opposite effect.
    """
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    philmanu_m1 = ts_mean(philmanu, window=month)
    philmanu_ml69 = ts_mean(philmanu, window=months_69)
    philmanu_p1m1ml69 = safe_div((philmanu_m1 - philmanu_ml69), philmanu_m1)
    philmanu_d1ml69ar_zn = zscore(philmanu_p1m1ml69, window=annual)
    return philmanu_d1ml69ar_zn