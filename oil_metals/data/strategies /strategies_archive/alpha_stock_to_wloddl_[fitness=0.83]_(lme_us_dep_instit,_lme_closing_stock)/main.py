config = AlphaConfig()
def alpha_stock_to_wloddl(
        s: Streams,
        delay=5,
        window=60
):
    """
    Hypothesis: Following the ratio of closing stocks and WLODLL,
    trying to detect small inventory levels in the weak economy periods
    """
    dep = ts_delay(ts_ffill(s.lme_us_dep_instit), delay)
    res = ts_pct_change(safe_div(s.lme_closing_stock, dep), window)

    return -res