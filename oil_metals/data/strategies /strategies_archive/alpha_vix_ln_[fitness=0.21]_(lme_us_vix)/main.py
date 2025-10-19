config = AlphaConfig()
def alpha_vix_ln(s: Streams):
    """
    Hypothesis: Rising market uncertainty (as indicated by an increase in the U.S. volatility index)
    over last month [based on logarithm] may signal potential high inflation, declining consumer demand, and reduced production.
    This scenario could lead to overproduction, shrinking base metal demand, and falling prices.
    """
    us_vix = s.lme_us_vix
    us_vix_ln = log(us_vix, base=10)
    us_vix_ln_ma15 = ts_mean(us_vix_ln, window=week_3)
    us_vix_ln_ma20 = delta(us_vix_ln_ma15, period=week)
    us_vix_ma_20_15 = us_vix_ln_ma20 - us_vix_ln_ma15
    return - us_vix_ma_20_15