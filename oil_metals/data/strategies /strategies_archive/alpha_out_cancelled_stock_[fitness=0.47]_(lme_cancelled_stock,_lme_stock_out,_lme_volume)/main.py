config = AlphaConfig()
def alpha_out_cancelled_stock(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: lme_stock_out >= SMA (16-day) AND lme_cancelled_stock <= SMA (8-day).
    - Short: lme_stock_out < SMA (16-day) AND lme_cancelled_stock > SMA (8-day).
    """

    lme_stock_out=s.lme_stock_out
    lme_cancelled_stock=s.lme_cancelled_stock
    sma1 = ts_mean(lme_stock_out, window=16)
    sma2 = ts_mean(lme_cancelled_stock, window=8)

    result = (lme_stock_out >= sma1) & (lme_cancelled_stock <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (lme_stock_out < sma1) & (lme_cancelled_stock > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * -s.lme_volume)+ (result2* -s.lme_volume )