config = AlphaConfig(neutralization = 'market')
def alpha_stock_in_n_out_clip(
        s: Streams,
        window=5,
        clip_level=0.05
) -> pd.DataFrame:
    """
    Hypothesis: calculate the change in asset's supply relative to the overall closing stock
    """

    res = ts_sum(s.lme_stock_out - s.lme_stock_in, window)
    res = safe_div(res, s.lme_closing_stock)
    res = ts_clip(res, -clip_level, clip_level)

    return res