config = AlphaConfig()
def alpha_dep_tres_perc_diff(s: Streams):
    """
    Hypothesis: Positive normalized percent difference between Deposits of banks and non-banking institutions
    at the Federal Reserve and the Treasury Balance may signal economic growth in the U.S.,
    leading to sustained demand for base metals and a corresponding rise in their prices.
    """
    dep_instit_diff = delta(ts_ffill(s.lme_us_dep_instit), period=week_2)
    tres_bal_diff = delta(ts_ffill(s.lme_us_tres_bal), period=week_2)
    dep_instit_tres_bal_diff = dep_instit_diff - tres_bal_diff
    return zscore(dep_instit_tres_bal_diff, window=month)