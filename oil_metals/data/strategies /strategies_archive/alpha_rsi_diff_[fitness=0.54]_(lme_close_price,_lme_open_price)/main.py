config = AlphaConfig(neutralization = 'market')
def alpha_rsi_diff(
        s: Streams,
        window=14
) -> pd.DataFrame:
    """
    Hypothesis: RSI indicator shows the strength of the price trend.
    Compare the strength at the beginning and the end of the day
    to calculate the changes in trading activity.

    NOTE: with some parameters Sharpe value could be 2.0, but it was
    optimized for turnover
    """

    rsi_close = ts_rsi(s.lme_close_price, window)
    rsi_open = ts_rsi(s.lme_open_price, window)

    result = rsi_open - rsi_close
    result = ts_ewm(result, span=4, min_periods=4)

    return rank(result)