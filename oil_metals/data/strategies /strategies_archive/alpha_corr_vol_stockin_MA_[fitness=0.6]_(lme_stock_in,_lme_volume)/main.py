config = AlphaConfig()
def alpha_corr_vol_stockin_MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: postivive correlation (lme_volume and lme_stock_in) * lme_volume <= SMA (4-day).
    - Short: negative correlation (lme_volume and lme_stock_in) * lme_volume > SMA (4-day).
    """

    series1 = s.lme_volume
    series2 = s.lme_stock_in
    ver1=s.lme_volume
    sma1 = ts_mean(ver1, window=4)
    corr = correlation(series1, series2, window=4)

    result = (ver1 <= sma1)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (ver1 > sma1)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )