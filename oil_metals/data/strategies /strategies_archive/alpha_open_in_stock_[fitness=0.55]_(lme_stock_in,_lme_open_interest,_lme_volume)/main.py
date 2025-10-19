config = AlphaConfig()
def alpha_open_in_stock(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: lme_open_interest <= SMA (5-day) AND lme_stock_in <= SMA (16-day).
    - Short: lme_open_interest > SMA (5-day) AND lme_stock_in > SMA (16-day).
    """

    lme_open_interest=s.lme_open_interest
    lme_stock_in=s.lme_stock_in
    sma1 = ts_mean(lme_open_interest, window=5)
    sma2 = ts_mean(lme_stock_in, window=16)

    result = (lme_open_interest <= sma1) & (lme_stock_in <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (lme_open_interest > sma1) & (lme_stock_in > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * s.lme_volume)+ (result2* s.lme_volume )