config = AlphaConfig()
def alpha_cny_on_warrant_div(
        s: Streams,
        window=5,
        clip_level=0.1
) -> pd.DataFrame:
    """
    Hypothesis: Check the ratio of CHY currency to the on warrant stock. If it has been changed over the past week, 
    expect price to go up and vice versa.
    """
    result = safe_div(s.lme_fx_cny, s.lme_on_warrant).pct_change(window)
    result = ts_clip(result, -clip_level, clip_level)

    return result