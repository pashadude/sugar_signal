config = AlphaConfig()
def alpha_fed_assets_tres_diff(s: Streams):
    """
    Hypothesis: Positive growth rate of the Federal Assets balance relative to the Treasury Balance
    may signal an increase in money supply, potentially boosting demand for base metals and driving up their prices.
    """
    fed_assets_diff = delta(s.lme_us_fed_assets.ffill(), period=week)
    tres_bal_diff = delta(s.lme_us_tres_bal.ffill(), period=week)
    fed_assets_prev = ts_delay(fed_assets_diff, period=week)
    tres_bal_prev = ts_delay(tres_bal_diff, period=week)
    fed_assets_ratio = safe_div(fed_assets_diff, fed_assets_prev)
    tres_bal_ratio = safe_div(tres_bal_diff, tres_bal_prev)
    fed_assets_tres_change = fed_assets_ratio - tres_bal_ratio
    return fed_assets_tres_change