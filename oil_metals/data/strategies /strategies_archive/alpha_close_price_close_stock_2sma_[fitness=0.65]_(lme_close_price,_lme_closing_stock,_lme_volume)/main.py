config = AlphaConfig()
def alpha_close_price_close_stock_2sma(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: lme_closing_stock <= SMA (3-day) AND lme_close_price <= SMA (2-day).
    - Short: lme_closing_stock > SMA (3-day) AND lme_close_price > SMA (2-day).
    """

    ver1=s.lme_closing_stock
    ver2=s.lme_close_price
    sma1 = ts_mean(ver1, window=3)
    sma2 = ts_mean(ver2, window=2)

    result = (ver1 <= sma1) & (ver2 <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (ver1 > sma1) & (ver2 > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * s.lme_volume) + (result2  * s.lme_volume )