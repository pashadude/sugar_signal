config = AlphaConfig()
def alpha_relative_price_correlations_2(
        s: Streams,
        window=10,
        clip_level=2
):
    """
    Hypothesis: relative daily price volatility correlation to the daily range of
    the prices' correlation. If this value changes a lot,
    it could indicate the shift of the price behaviour pattern
    """

    high = s.lme_high_price
    low = s.lme_low_price
    open = s.lme_open_price
    close = s.lme_close_price

    # calculate relative correlations
    numerator = correlation(high, low, window)
    denominator = correlation(close, open, window)
    res = numerator / denominator

    # clip the values
    res = ts_clip(res, -clip_level, clip_level)

    # normalize the values
    res = -zscore(res, 60)

    # find the change of values for window
    res = delta(res, window)

    return res