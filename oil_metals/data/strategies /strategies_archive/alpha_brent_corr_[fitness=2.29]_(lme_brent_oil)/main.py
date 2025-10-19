config = AlphaConfig()
def alpha_brent_corr(
        s: Streams,
        clip_const=4.5
) -> pd.DataFrame:
    """
    Hypothesis: current alpha enhances the "alpha_brent_no_delay" by incorporating
    1-day and 1-week delayed signals and adding clipping to reduce the turnover.
    As a result, more reliable trading signal is achieved
    """
    res = s.lme_brent_oil.copy()
    res[:] = 0
    delays = [0, 1, 5]

    for delay in delays:
        res = res + brent_stock_out_corr(s, delay_window=delay)
        res = res + brent_on_warrant_corr(s, delay_window=delay)
        res = res + brent_fed_assets_corr(s, delay_window=delay)

    res = ts_clip(res, -clip_const, clip_const)

    return res