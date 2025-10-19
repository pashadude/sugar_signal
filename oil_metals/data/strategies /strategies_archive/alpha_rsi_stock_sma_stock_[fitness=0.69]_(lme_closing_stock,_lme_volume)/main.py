config = AlphaConfig()
def alpha_rsi_stock_sma_stock(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (15-day) lme_volume < 45 AND lme_closing_stock ≤ SMA (10-day).
    - Short: RSI (15-day) lme_volume > 75 AND lme_closing_stock > SMA (10-day).
    """

    lme_volume=s.lme_volume
    lme_closing_stock=s.lme_closing_stock
    rsi_close_price = ts_rsi(lme_volume, period=15)
    sma = ts_mean(lme_closing_stock, window=10)

    result = (rsi_close_price < 45) & (lme_closing_stock <= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_short = (rsi_close_price > 55) & (lme_closing_stock >= sma)
    result_short = ts_where(result_short, result_short == True, 0)
    result_short = ts_where(result_short, result_short != True, -1)

    return ( result * s.lme_volume)+ (result_short* s.lme_volume )