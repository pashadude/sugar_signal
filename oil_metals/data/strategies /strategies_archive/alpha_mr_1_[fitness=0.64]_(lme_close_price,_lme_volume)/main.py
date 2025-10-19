config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_mr_1(s: Streams, window=21, standardise=True):
    """
    Mean reversion on Price, weighted by Volume levels.
    Hypothesis:
        - If price is above its recent average, we expect it to revert downward.
        - The stronger the Volume, the bigger the anticipated 'snap back'.
        - A longer window (21) reduces turnover.
    """
    # Smooth the price and volume
    price_smooth = ts_mean(s.lme_close_price, window)
    volume_smooth = ts_mean(s.lme_volume, window)

    # Price deviation from its rolling mean
    price_dev = price_smooth - ts_mean(price_smooth, window)

    # Weight by Volume (the greater the volume, the stronger the signal)
    # Multiply price_dev by negative one for mean reversion (long if negative, short if positive)
    result = -price_dev * (volume_smooth / (volume_smooth.mean() + 1e-6))

    if standardise:
        result = zscore(result)
    return result