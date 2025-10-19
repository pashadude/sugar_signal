config = AlphaConfig()
def alpha_rsi_sma_2(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (17-day) < 25 AND Closing Price ≤ SMA (2-day).
    - Short: RSI (17-day) > 75 AND Closing Price > SMA (2-day).
    """
    lme_close_price = s.lme_close_price
    rsi_close_price = ts_rsi(lme_close_price, period=17)
    sma = ts_mean(lme_close_price, window=2)

    result = (rsi_close_price <= 25) & (lme_close_price <= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_short = (rsi_close_price >= 75) & (lme_close_price > sma)
    result_short = ts_where(result_short, result_short == True, 0)
    result_short = ts_where(result_short, result_short != True, -1)

    return ( result * s.lme_volume)+ (result_short* s.lme_volume )