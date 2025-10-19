config = AlphaConfig(neutralization = 'market')
def alpha_rsi_close_direction(
        s: Streams,
        window=14
) -> pd.DataFrame:
    """
    Hypothesis: Based only on RSI indicator for close price and 30-70 boundaries,
    determine the direction of the price movements
    """

    rsi = ts_rsi(s.lme_close_price, window)

    rsi_direction = rsi.copy()
    rsi_direction[rsi >= 0] = 1
    rsi_direction[rsi >= 30] = 0
    rsi_direction[rsi >= 70] = -1

    return rsi_direction