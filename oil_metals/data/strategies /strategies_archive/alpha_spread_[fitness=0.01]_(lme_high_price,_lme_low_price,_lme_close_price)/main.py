config = AlphaConfig(neutralization = 'market')
def alpha_spread(
    s: Streams,
    window=5
) -> pd.DataFrame:
    """
    Hypothesis: spread of the prices for the day. Test version
    """
    df = safe_div(s.lme_high_price - s.lme_low_price, s.lme_close_price)
    df = ts_mean(df, window)

    return df