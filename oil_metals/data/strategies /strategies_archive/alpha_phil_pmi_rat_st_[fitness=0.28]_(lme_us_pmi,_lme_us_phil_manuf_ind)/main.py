config = AlphaConfig()
def alpha_phil_pmi_rat_st(s: Streams):
    """
    # Hypothesis: A positive ratio of the Philadelphia Fed Manufacturing Index to the Producers Manufacturing Index
    # in the short term indicates stronger regional manufacturing momentum compared to the national level,
    # suggesting increased demand for base metals and a corresponding rise in their prices and vise versa.
    """
    ## PHILMANU_SA_D3M3ML3_ZN
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    latest_3m = ts_mean(philmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    philmanu_d3m3ml3 = (latest_3m - previous_3m)
    philmanu_d3m3ml3_zn = zscore(philmanu_d3m3ml3, window=quarterly)

    ## ISMMANU_SA_D3M3ML3_ZN
    ismmanu = ts_ffill(s.lme_us_pmi)
    latest_3m = ts_mean(ismmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    issmanu_d3m3ml3 = (latest_3m - previous_3m)
    issmanu_d3m3ml3_zn = zscore(issmanu_d3m3ml3, window=quarterly)

    return safe_div(philmanu_d3m3ml3_zn, issmanu_d3m3ml3_zn)