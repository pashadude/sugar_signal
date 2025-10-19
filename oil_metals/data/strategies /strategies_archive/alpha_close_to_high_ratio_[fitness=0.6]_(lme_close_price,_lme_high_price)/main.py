config = AlphaConfig(assets = ['CMAL3', 'CMCU3', 'CMNI3', 'CMPB3', 'CMZN3'], neutralization = 'market')
def alpha_close_to_high_ratio(
        s: Streams,
        window=5,
        factor=0.5
):
    """
    Hypothesis: lower close to high price ratio might indicate bearish movement.
    Also normalizing & smoothing the values in three steps to reduve turnover
    """
    res = -safe_div(
        s.lme_close_price,
        s.lme_high_price
    )
    res = zscore(res, window)

    res = ts_decay_exp_window(res, window, factor)
    res = ts_decay_exp_window(res, window, factor)
    res = ts_decay_exp_window(res, window, factor)

    return res