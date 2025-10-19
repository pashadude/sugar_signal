config = AlphaConfig()
def alpha_rsi_stock_sma_interest(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (16-day) lme_closing_stock < 30 AND lme_open_interest ≤ SMA (5-day).
    - Short: RSI (16-day) lme_closing_stock > 70 AND lme_open_interest > SMA (5-day).
    """

    lme_closing_stock=s.lme_closing_stock
    lme_open_interest=s.lme_open_interest
    rsi_close_price = ts_rsi(lme_closing_stock, period=16)
    sma = ts_mean(lme_open_interest, window=5)

    result = (rsi_close_price <= 30) & (lme_open_interest <= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_short = (rsi_close_price >= 70) & (lme_open_interest >= sma)
    result_short = ts_where(result_short, result_short == True, 0)
    result_short = ts_where(result_short, result_short != True, -1)

    return ( result * s.lme_volume)+ (result_short* s.lme_volume )