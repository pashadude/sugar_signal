config = AlphaConfig()
def alpha_rsi_price_sma_stock_2(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (30-day) close price > 55 AND closing stock < SMA (10-day).
    - Short: RSI (30-day) close price > 45 AND closing stock > SMA (10-day).
    """
    lme_close_price = s.lme_close_price
    lme_closing_stock=s.lme_closing_stock
    rsi_close_price = ts_rsi(lme_close_price, period=30)
    sma = ts_mean(lme_closing_stock, window=10)

    result = (rsi_close_price <= 45) & (lme_closing_stock >= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_2 = (rsi_close_price >= 55) & (lme_closing_stock <= sma)
    result_2 = ts_where(result_2, result_2 == True, 0)
    result_2 = ts_where(result_2, result_2 != True, -1)

    return ( result * -s.lme_volume)+ (result_2* -s.lme_volume )