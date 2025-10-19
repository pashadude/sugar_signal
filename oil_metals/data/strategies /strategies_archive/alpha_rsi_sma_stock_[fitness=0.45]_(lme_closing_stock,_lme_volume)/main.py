config = AlphaConfig()
def alpha_rsi_sma_stock(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (14-day) closing stock < 25 AND closing stock ≤ SMA (26-day).
    - Short: RSI (14-day) closing stock > 75 AND closing stock > SMA (26-day).
    """
    lme_closing_stock=s.lme_closing_stock
    rsi_close_price = ts_rsi(lme_closing_stock, period=14)
    sma = ts_mean(lme_closing_stock, window=26)

    result = (rsi_close_price <= 25) & (lme_closing_stock <= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_short = (rsi_close_price >= 75) & (lme_closing_stock >= sma)
    result_short = ts_where(result_short, result_short == True, 0)
    result_short = ts_where(result_short, result_short != True, -1)

    return ( result * s.lme_volume)+ (result_short* s.lme_volume )