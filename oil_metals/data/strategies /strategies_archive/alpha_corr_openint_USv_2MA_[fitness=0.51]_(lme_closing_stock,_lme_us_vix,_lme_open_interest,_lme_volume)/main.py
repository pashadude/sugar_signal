config = AlphaConfig()
def alpha_corr_openint_USv_2MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: postivive correlation (lme_open_interest and lme_us_vix) * lme_closing_stock <= SMA (3-day) and <= SMA (14-day).
    - Short: negative correlation (lme_open_interest and lme_us_vix) * lme_closing_stock > SMA (3-day) and > SMA (14-day).
    """

    series1 = s.lme_open_interest
    series2 = s.lme_us_vix
    ver1=s.lme_closing_stock
    ver2=s.lme_closing_stock
    sma1 = ts_mean(ver1, window=3)
    sma2 = ts_mean(ver2, window=14)
    corr = correlation(series1, series2, window=40)

    result = (ver1 <= sma1) & (ver2 <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (ver1 > sma1) & (ver2 > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )