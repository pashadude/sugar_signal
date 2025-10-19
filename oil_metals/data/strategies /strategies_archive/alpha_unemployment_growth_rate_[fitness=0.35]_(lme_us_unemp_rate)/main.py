config = AlphaConfig()
def alpha_unemployment_growth_rate(s:Streams):
    """
    Hypothesis: Increase in the seasonally adjusted unemployment rate may indicate a potential inflation shock
    due to a labor supply deficit and shrinking of production, leading to reduced demand for base metals and a later drop in their prices.
    """
    tur = ts_ffill(s.lme_us_unemp_rate)
    tur_growth_rate = safe_div(delta(tur, period=month_2), ts_delay(tur, period=month_2))
    return zscore(tur_growth_rate, window=month_2)