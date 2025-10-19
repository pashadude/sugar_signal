config = AlphaConfig()
def alpha_corr_vol_low_MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: postivive correlation (lme_volume and lme_low_price) * lme_close_price <= SMA (30-day).
    - Short: negative correlation (lme_volume and lme_low_price) * lme_close_price > SMA (30-day).
    """

    series1 = s.lme_volume
    series2 = s.lme_low_price
    ver1=s.lme_closing_stock
    sma1 = ts_mean(ver1, window=38)
    corr = correlation(series1, series2, window=30)

    result = (ver1 <= sma1)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (ver1 > sma1)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )