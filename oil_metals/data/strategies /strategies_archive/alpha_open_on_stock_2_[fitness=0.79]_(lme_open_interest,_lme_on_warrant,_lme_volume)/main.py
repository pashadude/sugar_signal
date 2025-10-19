config = AlphaConfig()
def alpha_open_on_stock_2(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: lme_open_interest <= SMA (6-day) AND lme_on_warrant <= SMA (12-day).
    - Short: lme_open_interest < SMA (6-day) AND lme_on_warrant > SMA (12-day).
    """

    lme_open_interest=s.lme_open_interest
    lme_on_warrant=s.lme_on_warrant
    sma1 = ts_mean(lme_open_interest, window=6)
    sma2 = ts_mean(lme_on_warrant, window=12)

    result = (lme_open_interest <= sma1) & (lme_on_warrant <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (lme_open_interest > sma1) & (lme_on_warrant > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * s.lme_volume)+ (result2* s.lme_volume )