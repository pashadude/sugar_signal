config = AlphaConfig()
def alpha_m2_growth_rate(s:Streams):
    """
    Hypothesis: Higher money supply (M2) growth increases liquidity on the financial market,
    supporting inflation and steady base metals demand with their prices.
    """
    m2 = ts_ffill(s.lme_us_mon_sup)
    m2_growth_rate = safe_div(delta(m2, period=month_2), ts_delay(m2, period=month_2))
    return m2_growth_rate