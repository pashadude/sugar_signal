config = AlphaConfig()
def alpha_t10y2y(
        s: Streams,
        window1=10,
        window2=60
):
    """
    Hypothesis: Capturing the relative changes of T10Y2Y across different fields: VIX, inventories & price levels
    gives us different sides of influence of this indicator
    """
    res = ts_pct_change(
        safe_div(
            ts_ffill(s.lme_us_10_2_rate),
            ts_ffill(s.lme_close_price)
        ),
        window1
    )

    res = res + ts_pct_change(
        safe_div(
            ts_ffill(s.lme_us_10_2_rate),
            ts_ffill(s.lme_us_vix)
        ),
        window1
    )

    res = res + ts_pct_change(
        safe_div(
            ts_ffill(s.lme_us_10_2_rate),
            ts_ffill(s.lme_on_warrant)
        ),
        window2
    )

    return res