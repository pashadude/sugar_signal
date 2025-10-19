config = AlphaConfig()
def alpha_ip_phil_b_diff_st(s: Streams):
    """
    # Hypothesis: Rising industrial production and manufacturing activity in short-term, adjusting by inventory changes,
    # signals stronger demand and price support for base metals.
    """
    ## IP_SA_P3M3ML3AR_ZN
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    latest_3m = ts_mean(ip, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    ip_p3m3ml3ar = pct_change_3m * 4
    ip_p3m3ml3ar_zn = zscore(ip_p3m3ml3ar, window=quarterly)

    # PHILMANU_SA_D3M3ML3_ZN
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    latest_3m = ts_mean(philmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    philmanu_d3m3ml3 = (latest_3m - previous_3m)
    philmanu_d3m3ml3_zn = zscore(philmanu_d3m3ml3, window=quarterly)

    # BINVENTORIES_SA_P3M3ML3AR_ZN
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    latest_3m = ts_mean(bus_inv, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    bus_inv_p3m3ml3ar = pct_change_3m * 4
    bus_inv_p3m3ml3ar_zn = zscore(bus_inv_p3m3ml3ar, window=quarterly)

    return (ip_p3m3ml3ar_zn + philmanu_d3m3ml3_zn) - bus_inv_p3m3ml3ar_zn