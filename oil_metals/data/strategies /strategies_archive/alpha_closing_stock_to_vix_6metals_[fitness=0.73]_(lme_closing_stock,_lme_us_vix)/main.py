config = AlphaConfig()
def alpha_closing_stock_to_vix_6metals(
        s: Streams
):
    """
    Hypothesis: lower level of stock with the higher level of VIX might indicate the mean reversion
    and that people coming for the commodities in the volatile times, so that can boost the price up.
    Plus an additional double smoothing applied
    """
    res = -safe_div(zscore(s.lme_closing_stock), s.lme_us_vix)
    res = ts_mean(res, 5)
    res = ts_mean(res, 30)

    return res