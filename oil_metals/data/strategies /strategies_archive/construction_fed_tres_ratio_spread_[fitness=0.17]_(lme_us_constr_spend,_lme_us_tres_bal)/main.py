config = AlphaConfig()
def construction_fed_tres_ratio_spread(s:Streams):
    """
    Hypothesis: The Construction-Treasury Balance Spread tracks the relative growth of U.S. construction spending vs. Treasury balance changes.
    A declining spread may signal weaker demand, potentially lowering base metal prices.
    """
    construction_pct_zn = zscore(ts_mean(ts_pct_change(ts_ffill(s.lme_us_constr_spend), periods=month), window=month), window=month)
    tres_bal_pct_zn = zscore(ts_mean(ts_pct_change(ts_ffill(s.lme_us_tres_bal), periods=week), window=week), window=week)
    construction_fed_bal_spread = delta(safe_div(construction_pct_zn, tres_bal_pct_zn))
    return - construction_fed_bal_spread