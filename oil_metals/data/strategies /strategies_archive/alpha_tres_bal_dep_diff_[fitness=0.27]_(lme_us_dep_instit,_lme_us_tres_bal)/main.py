config = AlphaConfig()
def alpha_tres_bal_dep_diff(s: Streams):
    """
    Hypothesis: If the growth rate of the Deposits of banks and non-banking institutions at the Federal Reserve
    significantly exceeds the Treasury Balance, it may signal economic growth, potentially pushing demand
    for base metals and leading to a rise in their prices.
    """
    tres_bal_diff = delta(ts_ffill(s.lme_us_tres_bal), period=week)
    dep_instit_diff = delta(ts_ffill(s.lme_us_dep_instit), period=week)
    tres_bal_prev = ts_delay(tres_bal_diff, period=week)
    dep_instit_prev = ts_delay(dep_instit_diff, period=week)
    tres_bal_ratio = safe_div(tres_bal_diff, tres_bal_prev)
    dep_instit_ratio = safe_div(dep_instit_diff, dep_instit_prev)
    deposit_tres_change = tres_bal_ratio - dep_instit_ratio
    return deposit_tres_change