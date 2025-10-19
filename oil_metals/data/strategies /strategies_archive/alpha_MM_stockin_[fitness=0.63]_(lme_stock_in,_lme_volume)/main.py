config = AlphaConfig()
def alpha_MM_stockin(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: Middle 20, min-max (lme_stock_in) > Middle 5, min-max (lme_stock_in)
    - Short: Middle 20, min-max (lme_stock_in) <= Middle 5, min-max (lme_stock_in)
    """
    
    Middle1 = (ts_max(s.lme_stock_in, window=20) + ts_min(s.lme_stock_in, window=20)) / 2
    Middle2 = (ts_max(s.lme_stock_in, window=5) + ts_min(s.lme_stock_in, window=5)) / 2

    result = (Middle1 <= Middle2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (Middle1 > Middle2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * -s.lme_volume) + (result2 * -s.lme_volume )