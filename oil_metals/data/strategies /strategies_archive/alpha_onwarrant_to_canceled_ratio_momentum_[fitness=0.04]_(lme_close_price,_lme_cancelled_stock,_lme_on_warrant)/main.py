config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_onwarrant_to_canceled_ratio_momentum(s: Streams, window=5, standardise=True):
    onwarrant = ts_mean(s.lme_on_warrant, window=window)
    canceled = ts_mean(s.lme_cancelled_stock, window=window)
    ratio = safe_div(onwarrant, canceled)
    ratio_mom = delta(ratio, period=window)
    
    price_mom = ts_mean(s.lme_close_price) - ts_mean(s.lme_close_price, window=window)
    # If ratio_mom < 0 (scarcity rising) but price hasn’t caught up (price_mom <= 0), bullish
    result = (-ratio_mom) * (-price_mom)  # Two negatives = positive if both declining ratio and lagging price
    if standardise:
        result = zscore(result)
    return -result