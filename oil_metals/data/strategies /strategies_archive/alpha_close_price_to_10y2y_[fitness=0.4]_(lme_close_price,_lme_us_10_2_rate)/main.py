config = AlphaConfig()
def alpha_close_price_to_10y2y(
        s: Streams,
        window=10
):
    """
    Hypothesis: Rapid change in ratio of close price to T10Y2Y might indicate shift in the economy period
    """
    res = safe_div(
        ts_ffill(s.lme_close_price),
        ts_ffill(s.lme_us_10_2_rate)
    )

    return -ts_pct_change(res, window)