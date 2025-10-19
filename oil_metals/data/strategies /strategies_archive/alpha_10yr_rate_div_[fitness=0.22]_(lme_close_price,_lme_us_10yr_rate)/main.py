config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_10yr_rate_div(s: Streams, window=20, smooth_window=5):
    """
    Compare short-term changes in US 10yr rate to changes in the metal's price.
    Hypothesis (Real Cost of Capital):
      - Rising yields can strengthen the dollar and weigh on metals,
        or signal improved growth and thus higher metal demand—test direction via backtest.
      - Divergence can reveal shifts in macro vs. metal-specific drivers.
    """
    rate_change = delta(s.lme_us_10yr_rate, period=window)
    metal_change = delta(s.lme_close_price, period=window)
    
    div_raw = rate_change - metal_change
    div_smooth = ts_mean(div_raw, window=smooth_window)
    return -div_smooth