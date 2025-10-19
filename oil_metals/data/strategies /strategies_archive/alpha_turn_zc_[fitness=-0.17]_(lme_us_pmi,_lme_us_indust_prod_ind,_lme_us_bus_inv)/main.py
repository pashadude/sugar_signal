config = AlphaConfig()
def alpha_turn_zc(s: Streams):
    """
    Hypothesis: Signal which combines the Purchasing Managers' Index (PMI) and a weighted business inventory measure, reflects the interplay between medium-term economic activity and inventory levels.
    An increase in this signal suggests rising business activity, driven by a higher PMI, alongside a moderate inventory effect, potentially boosting base metals demand and prices.
    Conversely, a decrease in the signal may indicate weaker economic activity and excess inventory, leading to reduced demand and falling prices for base metals.
    """
    ## ISMMANU_SA_D3M3ML3_ZN
    ismmanu = ts_ffill(s.lme_us_pmi)
    latest_3m = ts_mean(ismmanu, window=quarterly)
    previous_3m = ts_delay(latest_3m, period=quarterly)
    issmanu_d3m3ml3 = (latest_3m - previous_3m)
    issmanu_d3m3ml3_zn = zscore(issmanu_d3m3ml3, window=month)
    ## IOMT_ZC
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
    ## "IOMT_ZC" = 0.5 * "BINVENTORIES_SA_P1M1ML12_3MMA_ZN" + 0.5 * "IP_SA_P1M1ML12_3MMA_ZN"
    iomt_zc = 0.5 * bus_inv_p1m1ml12_3mma_zn + 0.5 * ip_p1m1ml12_3mma_zn
    ## "TURN_ZC" = "IOMT_ZC" - 0.5 * "ISMMANU_SA_D3M3ML3_ZN"
    turn_zc = iomt_zc - 0.5 * issmanu_d3m3ml3_zn
    return turn_zc