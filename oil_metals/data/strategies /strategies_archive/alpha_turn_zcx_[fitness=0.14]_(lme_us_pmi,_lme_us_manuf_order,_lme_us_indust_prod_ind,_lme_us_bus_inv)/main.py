config = AlphaConfig()
def alpha_turn_zcx(s: Streams):
    """
    Hypothesis: Signal  combines the Purchasing Managers' Index (PMI) with business inventory and durable goods order measures, reflects the balance between short-term economic activity and overproduction.
    An increase in this signal suggests a positive outlook for base metals, driven by rising business activity (PMI) and balanced inventory levels, leading to higher demand and prices.
    Conversely, a decrease in the signal indicates weaker economic conditions, excess inventory, and declining demand, potentially leading to lower base metals prices
    """
    ## ISMMANU_SA_D3M3ML3_ZN
    ismmanu = ts_ffill(s.lme_us_pmi)
    latest_3m = ts_mean(ismmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    issmanu_d3m3ml3 = (previous_3m - latest_3m)
    issmanu_d3m3ml3_zn = zscore(issmanu_d3m3ml3, window=month_2)
    ## IOMT_ZC
    ## BINVENTORIES_SA_P1M1ML12_3MMA_ZN
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    bus_inv_pct_change = ts_pct_change(bus_inv, periods=annual)
    bus_inv_p1m1ml12_3mma = ts_mean(bus_inv_pct_change, window=quarterly)
    bus_inv_p1m1ml12_3mma_zn = zscore(bus_inv_p1m1ml12_3mma, window=month_2)
    ## IP_SA_P1M1ML12_3MMA_ZN
    ip = ts_ffill(s.lme_us_indust_prod_ind)
    ip_pct_change = ts_pct_change(ip, periods=annual)
    ip_p1m1ml12_3mma = ts_mean(ip_pct_change, window=quarterly)
    ip_p1m1ml12_3mma_zn = zscore(ip_p1m1ml12_3mma, window=month_2)
    ## IOMT_ZC" = 0.5 * "BINVENTORIES_SA_P1M1ML12_3MMA_ZN" + 0.5 * "IP_SA_P1M1ML12_3MMA_ZN
    iomt_zc = 0.5 * bus_inv_p1m1ml12_3mma_zn + 0.5 * ip_p1m1ml12_3mma_zn
    ## BINVENTORIES_SA_P3M3ML3AR_ZN
    bus_inv = ts_ffill(s.lme_us_bus_inv)
    latest_3m = ts_mean(bus_inv, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    bus_inv_p3m3ml3ar = pct_change_3m * 4
    bus_inv_p3m3ml3ar_zn = zscore(bus_inv_p3m3ml3ar, window=month_2)
    ## DGORDERS_SA_P3M3ML3AR_ZN
    dgorders = ts_ffill(s.lme_us_manuf_order)
    latest_3m = ts_mean(dgorders, window=quarterly)
    previous_3m = ts_delay(latest_3m,period=quarterly)
    pct_change_3m = safe_div((latest_3m - previous_3m), previous_3m)
    dgorders_p3m3ml3ar = pct_change_3m * 4
    dgorders_p3m3ml3ar_zn = zscore(dgorders_p3m3ml3ar, window=month_2)
    ## IOST_ZC
    iost_zc = 0.5 * bus_inv_p3m3ml3ar_zn + 0.5 * dgorders_p3m3ml3ar_zn
    ## "TURN_ZCX" = "IOMT_ZC" - "IOST_ZC" - 0.5 * "ISMMANU_SA_D3M3ML3_ZN"
    turn_zcx = iomt_zc - iost_zc - 0.5 * issmanu_d3m3ml3_zn
    return turn_zcx