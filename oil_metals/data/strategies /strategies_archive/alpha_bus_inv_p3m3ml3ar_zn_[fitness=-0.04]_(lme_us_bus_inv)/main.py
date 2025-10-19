config = AlphaConfig()
def alpha_bus_inv_p3m3ml3ar_zn(s: Streams):
    """
    Hypothesis: An increase in business inventories in the short run may indicate stable demand for base metals
    with their price increasing. Conversely, the opposite effect may occur.
    """
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    latest_3m = ts_mean(bus_inv, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    bus_inv_p3m3ml3ar = pct_change_3m * 4
    bus_inv_p3m3ml3ar_zn = zscore(bus_inv_p3m3ml3ar, window=month)
    return bus_inv_p3m3ml3ar_zn