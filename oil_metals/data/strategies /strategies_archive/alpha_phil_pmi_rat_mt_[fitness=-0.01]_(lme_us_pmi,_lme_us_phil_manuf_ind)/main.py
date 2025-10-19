config = AlphaConfig()
def alpha_phil_pmi_rat_mt(s: Streams):
    """
    # Hypothesis: A positive ratio of the Philadelphia Fed Manufacturing Index to the Producers Manufacturing Index
    # in the medium term indicates stronger regional manufacturing momentum compared to the national level,
    # suggesting increased demand for base metals and a corresponding rise in their prices and vise versa.
    """
    ## PHILMANU_SA_3MMA_ZN
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    philmanu_3mma = ts_mean(philmanu, window=quarterly)
    philmanu_3mma_zn = zscore(philmanu_3mma, window=quarterly)

    ## ISMMANU_SA_3MMA_ZN
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_3mma = ts_mean(issmanu, window=quarterly)
    issmanu_3mma_zn = zscore(issmanu_3mma, window=quarterly)

    return safe_div(philmanu_3mma_zn, issmanu_3mma_zn)