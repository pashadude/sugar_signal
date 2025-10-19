config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_daily_mid_reversion(s: Streams):
    """
    Each day, estimate a 'midpoint' = (high_of_day + low_of_day)/2,
    then if close is above midpoint => short, else long. 
    This is a daily reversion concept.
    
    Note: This requires you have a 'high' and 'low' price in Streams, or at least
    a proxy. We'll assume s.lme_high_price, s.lme_low_price exist.
    """
    daily_mid = (s.lme_high_price + s.lme_low_price) / 2.0

    # If close > mid => short, if close < mid => long
    signal = s.lme_close_price - daily_mid
    return -signal