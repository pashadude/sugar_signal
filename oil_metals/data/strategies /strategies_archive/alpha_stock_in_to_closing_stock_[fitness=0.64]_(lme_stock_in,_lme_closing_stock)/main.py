config = AlphaConfig(neutralization = 'market')
def alpha_stock_in_to_closing_stock(
        s: Streams,
        window=5
) -> pd.DataFrame:
    """
    Hypothesis: relative rate of change of the incoming stock supply to the available stock supply
    can show us the increase in asset's supply.

    NOTE: winsorize could have some lookahead, need to implement it on moving window.
    """
    df = -safe_div(
        delta(s.lme_stock_in, window),
        delta(s.lme_closing_stock, window)
    )

    df = winsorize(df, 0.05)

    return ts_mean(df, window)