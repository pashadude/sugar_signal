config = AlphaConfig()
def alpha_iost_zc(s: Streams):
    """
    Hypothesis: Signal combines 50% of short-term business inventory changes and 50% of the 3-month trend in durable goods orders, represents the relationship between inventory levels and demand for durable goods.
    An increase in the signal may suggest that rising durable goods orders are strengthening short-term economic activity, potentially driving up base metals demand and prices.
    However, if business inventories are also rising, this could signal overproduction, potentially offsetting the demand boost and leading to price stabilization or decline.
    Conversely, a decrease in the signal may indicate weakening durable goods orders and potential overstocking, reducing base metals demand and causing prices to fall.
    """
    ## BINVENTORIES_SA_P3M3ML3AR_ZN
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    latest_3m = ts_mean(bus_inv, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    bus_inv_p3m3ml3ar = pct_change_3m * 4
    bus_inv_p3m3ml3ar_zn = zscore(bus_inv_p3m3ml3ar, window=month)
    ## DGORDERS_SA_P3M3ML3AR_ZN
    dgorders = ts_ffill(s.lme_us_manuf_order)
    latest_3m = ts_mean(dgorders, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    dgorders_p3m3ml3ar = pct_change_3m * 4
    dgorders_p3m3ml3ar_zn = zscore(dgorders_p3m3ml3ar, window=month)
    ## IOST_ZC
    iost_zc = 0.5 * bus_inv_p3m3ml3ar_zn + 0.5 * dgorders_p3m3ml3ar_zn
    return iost_zc