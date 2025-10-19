config = AlphaConfig()
def alpha_fed_rate_change(s:Streams):
    """
    Hypothesis: Increase in the Federal Funds Rate among commercial banks indicates higher borrowing costs,
    potentially slowing production growth, reducing base metal demand, and leading to a drop in their prices.
    """
    fed_rate = ts_ffill(s.lme_us_fed_rate)
    fed_rate_change = ts_pct_change(fed_rate, periods=month_2)
    return - fed_rate_change