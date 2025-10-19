config = AlphaConfig(neutralization = 'market')
def alpha_stock_in_to_closing_stock_2_6metals(
        s: Streams,
        window=5,
        clip_level=0.09
) -> pd.DataFrame:
    """
    Hypothesis: relative rate of change of the incoming stock supply to the available stock supply
    can show us the increase in asset's supply.
    """
    df = -safe_div(
        delta(s.lme_stock_in, window),
        delta(s.lme_closing_stock, window)
    )

    df = ts_mean(df, window)
    df = ts_clip(df, -clip_level, clip_level)
    df = ts_decay_exp_window(df, window, 0.5)

    return df