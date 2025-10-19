config = AlphaConfig()
def alpha_ip_phil_b_diff_mt(s: Streams):
    """
    Hypothesis: Rising industrial production and manufacturing activity in middle run, adjusting by inventory changes,
    signals stronger demand and price support for base metals
    """
    ## IP_SA_P1M1ML12_3MMA_ZN
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_pct_change = ts_pct_change(ip, periods=annual)
    ip_p1m1ml12_3mma = ts_mean(ip_pct_change, window=quarterly)
    ip_p1m1ml12_3mma_zn = zscore(ip_p1m1ml12_3mma, window=quarterly)

    ## PHILMANU_SA_3MMA_ZN
    philmanu = ts_ffill(s.lme_us_phil_manuf_ind)
    philmanu_3mma = ts_mean(philmanu, window=quarterly)
    philmanu_3mma_zn = zscore(philmanu_3mma, window=quarterly)

    ## BINVENTORIES_SA_P1M1ML12_3MMA_ZN
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    bus_inv_pct_change = ts_pct_change(bus_inv, periods=annual)
    bus_inv_p1m1ml12_3mma = ts_mean(bus_inv_pct_change, window=quarterly)
    bus_inv_p1m1ml12_3mma_zn = zscore(bus_inv_p1m1ml12_3mma, window=quarterly)

    return (ip_p1m1ml12_3mma_zn + philmanu_3mma_zn) - bus_inv_p1m1ml12_3mma_zn