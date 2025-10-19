config = AlphaConfig(neutralization = 'market')
def alpha_on_warrant_momentum(
        s: Streams,
        window=5,
        clip_level=0.02
) -> pd.DataFrame:
    """
    Hypothesis: go short if the available capacity of metal
    in the inventories keeps increasing in the previous 5-day window.
    Clip level is set to remove outliers from the data
    """

    res = -ts_mean(ts_pct_change(s.lme_on_warrant), window)
    res = ts_clip(res, -clip_level, clip_level)

    return res