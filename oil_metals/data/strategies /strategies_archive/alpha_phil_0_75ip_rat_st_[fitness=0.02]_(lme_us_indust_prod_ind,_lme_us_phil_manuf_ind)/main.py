config = AlphaConfig()
def alpha_phil_0_75ip_rat_st(s: Streams):
    """
    Hypothesis: An increase in manufacturing activity in the short term, compared to 75% of
    Industrial Production in the U.S. that specifically relates to a portion of total U.S. manufacturing,
    suggests a strong economy in the Philadelphia district.
    A positive value indicates potential excess demand, which could lead to higher base metal prices and vise versa.
    """
    ## PHILMANU_SA_D3M3ML3_ZN
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    latest_3m = ts_mean(philmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    philmanu_d3m3ml3 = (latest_3m - previous_3m)
    philmanu_d3m3ml3_zn = zscore(philmanu_d3m3ml3, window=quarterly)

    ## IP_SA_P3M3ML3AR_ZN
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    latest_3m = ts_mean(ip, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    ip_p3m3ml3ar = pct_change_3m * 4
    ip_p3m3ml3ar_zn = zscore(ip_p3m3ml3ar, window=quarterly)

    return safe_div(philmanu_d3m3ml3_zn, (0.75 * ip_p3m3ml3ar_zn))