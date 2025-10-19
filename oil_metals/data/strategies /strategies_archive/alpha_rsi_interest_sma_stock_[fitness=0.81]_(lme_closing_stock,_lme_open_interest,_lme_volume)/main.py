config = AlphaConfig()
def alpha_rsi_interest_sma_stock(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: RSI (13-day) lme_open_interest < 35 AND lme_closing_stock ≤ SMA (6-day).
    - Short: RSI (13-day) lme_open_interest > 65 AND lme_closing_stock > SMA (6-day).
    """

    lme_open_interest=s.lme_open_interest
    lme_closing_stock=s.lme_closing_stock
    rsi_close_price = ts_rsi(lme_open_interest, period=13)
    sma = ts_mean(lme_closing_stock, window=6)

    result = (rsi_close_price <= 35) & (lme_closing_stock <= sma)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result_short = (rsi_close_price >= 65) & (lme_closing_stock >= sma)
    result_short = ts_where(result_short, result_short == True, 0)
    result_short = ts_where(result_short, result_short != True, -1)

    return ( result * s.lme_volume)+ (result_short* s.lme_volume )