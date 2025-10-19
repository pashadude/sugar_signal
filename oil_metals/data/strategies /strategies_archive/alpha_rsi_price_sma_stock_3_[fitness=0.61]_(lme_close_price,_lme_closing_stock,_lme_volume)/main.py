config = AlphaConfig()
def alpha_rsi_price_sma_stock_3(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (33-day) close price < 70 AND closing stock < SMA (3-day).
    - Short: RSI (33-day) close price > 30 AND closing stock > SMA (3-day).
    """
    lme_close_price = s.lme_close_price
    lme_closing_stock=s.lme_closing_stock
    rsi_close_price = ts_rsi(lme_close_price, period=33)
    sma = ts_mean(lme_closing_stock, window=3)

    result = (rsi_close_price <= 70) & (lme_closing_stock <= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_short = (rsi_close_price >= 30) & (lme_closing_stock >= sma)
    result_short = ts_where(result_short, result_short == True, 0)
    result_short = ts_where(result_short, result_short != True, -1)

    return ( result * s.lme_volume)+ (result_short* s.lme_volume )