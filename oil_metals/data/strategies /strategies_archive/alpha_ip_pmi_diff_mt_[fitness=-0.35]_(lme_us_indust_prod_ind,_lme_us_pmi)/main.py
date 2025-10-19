config = AlphaConfig()
def alpha_ip_pmi_diff_mt(s: Streams):
    """
    # Hypothesis: An increase in the divergence between U.S. total industrial production
    # (encompassing manufacturing, mining, and utilities) and specified production in the medium term
    # may indicate additional demand from the mining and utilities sectors,
    # potentially driving higher demand and prices for base metals.
    # Conversely, a decrease in this divergence could suggest the opposite effect.
    """
    ## IP_SA_P1M1ML12_3MMA_ZN
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_pct_change = ts_pct_change(ip, periods=month)
    ip_p1m1ml12_3mma = ts_mean(ip_pct_change, window=quarterly)
    ip_p1m1ml12_3mma_zn = zscore(ip_p1m1ml12_3mma, window=quarterly)

    ## ISMMANU_SA_3MMA_ZN
    issmanu = ts_ffill(s.lme_us_pmi)
    issmanu_3mma = ts_mean(issmanu, window=quarterly)
    issmanu_3mma_zn = zscore(issmanu_3mma, window=quarterly)

    return ip_p1m1ml12_3mma_zn - issmanu_3mma_zn