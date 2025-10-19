config = AlphaConfig(assets = ['CMAL3', 'CMCU3', 'CMNI3', 'CMPB3', 'CMZN3'])
def alpha_relative_price_correlations(
        s: Streams,
        window=10,
        clip_level=2
):
    """
    Hypothesis: relative daily price volatility correlation to the daily range of
    the prices' correlation. If this value changes a lot,
    it could indicate the shift of the price behaviour pattern
    """

    # fetch the data
    high = s.lme_high_price
    low = s.lme_low_price
    open = s.lme_open_price
    close = s.lme_close_price

    # calculate relative correlations
    numerator = correlation(high, low, window)
    denominator = correlation(close, open, window)
    res = numerator / denominator

    # add a weight of a previous value to current one
    res = ts_decay_exp_window(res, 2, 0.5)

    # clip the values
    res = ts_clip(res, -clip_level, clip_level)

    # normalize the values
    res = -zscore(res, window)

    return res