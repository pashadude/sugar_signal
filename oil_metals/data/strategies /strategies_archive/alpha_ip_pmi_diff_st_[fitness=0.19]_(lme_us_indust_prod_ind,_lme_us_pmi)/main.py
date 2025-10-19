config = AlphaConfig()
def alpha_ip_pmi_diff_st(s: Streams):
    """
    # Hypothesis: An increase in the divergence between U.S. total industrial production
    # (encompassing manufacturing, mining, and utilities) and specified production in the short-term
    # may indicate additional demand from the mining and utilities sectors,
    # potentially driving higher demand and prices for base metals.
    # Conversely, a decrease in this divergence could suggest the opposite effect.
    """
    ## IP_SA_P3M3ML3AR_ZN
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    latest_3m = ts_mean(ip, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    ip_p3m3ml3ar = pct_change_3m * 4
    ip_p3m3ml3ar_zn = zscore(ip_p3m3ml3ar, window=quarterly)

    ## ISMMANU_SA_D3M3ML3_ZN
    ismmanu = ts_ffill(s.lme_us_pmi)
    latest_3m = ts_mean(ismmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    issmanu_d3m3ml3 = (latest_3m - previous_3m)
    issmanu_d3m3ml3_zn = zscore(issmanu_d3m3ml3, window=quarterly)

    return ip_p3m3ml3ar_zn - issmanu_d3m3ml3_zn