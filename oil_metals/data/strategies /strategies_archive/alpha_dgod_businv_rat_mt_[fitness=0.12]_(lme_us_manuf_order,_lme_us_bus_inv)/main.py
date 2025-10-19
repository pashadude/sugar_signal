config = AlphaConfig()
def alpha_dgod_businv_rat_mt(s: Streams):
    """
    # Hypothesis: Relationship between durable goods orders and business inventories in medium-term.
    # A rising ratio implies increasing demand relative to supply, signaling potential price pressure or market tightness for base metals.
    """
    ## DGORDERS_SA_P3M3ML3AR_ZN
    dgorders = ts_ffill(s.lme_us_manuf_order)
    dgorders_pct_change = ts_pct_change(dgorders, periods=annual)
    dgorders_p1maml12_3mma = ts_mean(dgorders_pct_change, window=quarterly)
    dgorders_p1maml12_3mma_zn = zscore(dgorders_p1maml12_3mma, window=quarterly)

    ## BINVENTORIES_SA_P3M3ML3AR_ZN
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    bus_inv_pct_change = ts_pct_change(bus_inv, periods=annual)
    bus_inv_p1m1ml12_3mma = ts_mean(bus_inv_pct_change, window=quarterly)
    bus_inv_p1m1ml12_3mma_zn = zscore(bus_inv_p1m1ml12_3mma, window=quarterly)

    return safe_div(dgorders_p1maml12_3mma_zn, bus_inv_p1m1ml12_3mma_zn)