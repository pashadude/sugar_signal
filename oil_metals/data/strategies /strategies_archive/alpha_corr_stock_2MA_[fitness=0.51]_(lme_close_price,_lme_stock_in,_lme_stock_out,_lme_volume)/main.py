config = AlphaConfig()
def alpha_corr_stock_2MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: positive correlation (lme_stock_in and lme_stock_out) * lme_close_price (<= SMA (6-day) AND <= SMA (7-day)).
    - Short: negative correlation (lme_stock_in and lme_stock_out) * lme_close_price (> SMA (6-day) AND > SMA (7-day)).
    """

    series1 = s.lme_stock_in
    series2 = s.lme_stock_out
    ver1=s.lme_close_price
    ver2=s.lme_close_price
    sma1 = ts_mean(ver1, window=6)
    sma2 = ts_mean(ver2, window=7)
    corr = correlation(series1, series2, window=22)

    result = (ver1 <= sma1) & (ver2 <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (ver1 > sma1) & (ver2 > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )