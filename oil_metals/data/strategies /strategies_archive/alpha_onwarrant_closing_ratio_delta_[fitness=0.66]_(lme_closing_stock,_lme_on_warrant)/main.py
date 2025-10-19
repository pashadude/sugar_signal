config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_onwarrant_closing_ratio_delta(s: Streams, ratio_window=14, delta_period=5):
    """
    Look at the rolling ratio of on-warrant to closing stock, 
    then see how it changes over 'delta_period' days.
    Hypothesis:
      - Rapid increases in the ratio => supply rising faster => bearish.
      - Rapid decreases => supply falling => bullish.
    """
    ratio = safe_div(s.lme_on_warrant, s.lme_closing_stock)
    ratio_smooth = ts_mean(ratio, window=ratio_window)
    return delta(ratio_smooth, period=delta_period)