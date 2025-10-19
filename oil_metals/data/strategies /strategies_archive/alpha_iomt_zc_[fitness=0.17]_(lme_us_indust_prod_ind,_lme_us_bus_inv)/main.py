config = AlphaConfig()
def alpha_iomt_zc(s: Streams):
    """
    Hypothesis: Interplay between supply dynamics (inventory levels) and production-driven demand (industrial production).
    An increase in the signal value may indicate a balance where industrial production growth offsets potential inventory overproduction,
    suggesting stable or increased demand for base metals, potentially supporting price growth. Conversely, a decline in the signal may
    reflect weakening industrial activity or excessive inventory accumulation, leading to reduced base metals demand and potential price decline.
    """
    ## BINVENTORIES_SA_P1M1ML12_3MMA_ZN
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    bus_inv_pct_change = ts_pct_change(bus_inv, periods=annual)
    bus_inv_p1m1ml12_3mma = ts_mean(bus_inv_pct_change, window=quarterly)
    bus_inv_p1m1ml12_3mma_zn = zscore(bus_inv_p1m1ml12_3mma, window=month)
    ## IP_SA_P1M1ML12_3MMA_ZN
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_pct_change = ts_pct_change(ip, periods=annual)
    ip_p1m1ml12_3mma = ts_mean(ip_pct_change, window=quarterly)
    ip_p1m1ml12_3mma_zn = zscore(ip_p1m1ml12_3mma, window=month)
    ## IOMT_ZC" = 0.5 * "BINVENTORIES_SA_P1M1ML12_3MMA_ZN" + 0.5 * "IP_SA_P1M1ML12_3MMA_ZN
    iomt_zc = 0.5 * bus_inv_p1m1ml12_3mma_zn + 0.5 * ip_p1m1ml12_3mma_zn
    return iomt_zc