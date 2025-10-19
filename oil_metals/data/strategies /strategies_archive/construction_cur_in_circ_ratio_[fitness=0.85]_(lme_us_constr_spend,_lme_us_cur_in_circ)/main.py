config = AlphaConfig()
def construction_cur_in_circ_ratio(s:Streams):
    """
    Hypothesis: The Construction-to-Currency Ratio compares U.S. construction spending growth to currency supply growth.
    A high ratio may signal overconstruction, outpacing liquidity, risking oversupply and weaker base metal demand.
    """
    constr_spend = ts_mean(ts_pct_change(ts_ffill(s.lme_us_constr_spend), periods=month), window=quarterly)
    cur_in_circ = ts_mean(ts_pct_change((ts_ffill(s.lme_us_cur_in_circ)), periods=week), window=week_3)
    construction_currency_ratio = zscore(safe_div(constr_spend, cur_in_circ), window=quarterly)
    return - construction_currency_ratio