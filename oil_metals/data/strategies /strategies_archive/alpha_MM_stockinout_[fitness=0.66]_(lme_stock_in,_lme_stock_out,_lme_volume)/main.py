config = AlphaConfig()
def alpha_MM_stockinout(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: postivive correlation (lme_open_interest and lme_us_vix) * lme_closing_stock <= SMA (3-day) and <= SMA (14-day).
    - Short: negative correlation (lme_open_interest and lme_us_vix) * lme_closing_stock > SMA (3-day) and > SMA (14-day).
    """
    
    Middle1 = (ts_max(s.lme_stock_out, window=21) + ts_min(s.lme_stock_out, window=21)) / 2
    Middle2 = (ts_max(s.lme_stock_in, window=21) + ts_min(s.lme_stock_in, window=21)) / 2

    result = (Middle1 <= Middle2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (Middle1 > Middle2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * s.lme_volume) + (result2 * s.lme_volume )