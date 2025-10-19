config = AlphaConfig()
def alpha_on_warrant_eu_cpi_6metals(
        s: Streams
):
    """
    Hypothesis: Correlation between on warrant LME stock and EU CPI (lagged by one month)
    could give us a hint of general economic state & activity

    Warning: although the alpha here uses the delay of 1M to remove lookahead,
    it is still very sensitive to even minor parameter change
    """
    res = -correlation(
        ts_ffill(s.lme_on_warrant),
        ts_delay(ts_ffill(s.lme_eu_cpi), 22),
        10
    )

    return res