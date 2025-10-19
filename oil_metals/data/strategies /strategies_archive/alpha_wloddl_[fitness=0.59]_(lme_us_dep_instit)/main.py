config = AlphaConfig()
def alpha_wloddl(
        s: Streams
):
    """
    Hypothesis: trying to detect weak economy cycles. In the weak economy demand for metals might rise
    """
    data = ts_delay(ts_ffill(s.lme_us_dep_instit), 1)

    return ts_mean(ts_pct_change(data, 60), 22)