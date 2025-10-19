config = AlphaConfig()
def alpha_rsi_price_sma_stock(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (14-day) close price < 25 AND closing stock ≤ SMA (27-day).
    - Short: RSI (14-day) close price > 75 AND closing stock > SMA (27-day).
    """
    lme_close_price = s.lme_close_price
    lme_closing_stock=s.lme_closing_stock
    rsi_close_price = ts_rsi(lme_close_price, period=14)
    sma = ts_mean(lme_closing_stock, window=27)

    result = (rsi_close_price <= 25) & (lme_closing_stock <= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_short = (rsi_close_price >= 75) & (lme_closing_stock >= sma)
    result_short = ts_where(result_short, result_short == True, 0)
    result_short = ts_where(result_short, result_short != True, -1)

    return ( result * s.lme_volume)+ (result_short* s.lme_volume )