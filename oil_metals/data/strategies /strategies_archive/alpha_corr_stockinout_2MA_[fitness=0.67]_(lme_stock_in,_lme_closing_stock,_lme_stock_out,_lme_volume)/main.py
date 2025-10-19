config = AlphaConfig()
def alpha_corr_stockinout_2MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: postivive correlation (lme_stock_in and lme_stock_out) * lme_closing_stock <= SMA (3-day) and <= SMA (13-day).
    - Short: negative correlation (lme_stock_in and lme_stock_out) * lme_closing_stock > SMA (3-day) and > SMA (13-day).
    """

    series1 = s.lme_stock_in
    series2 = s.lme_stock_out
    ver1=s.lme_closing_stock
    ver2=s.lme_closing_stock
    sma1 = ts_mean(ver1, window=3)
    sma2 = ts_mean(ver2, window=13)
    corr = correlation(series1, series2, window=12)

    result = (ver1 <= sma1) & (ver2 <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (ver1 > sma1) & (ver2 > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )