config = AlphaConfig()
def alpha_dual_sma_close_price_both(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: SMA(48 days) ≥ SMA(32 days) AND Closing Price ≥ SMA(48 days) AND Closing Price ≥ SMA(32 days)
    - Short: SMA(32 days) ≥ SMA(48 days) AND Closing Price < SMA(48 days) AND Closing Price < SMA(32 days)
    """
    sma01= ts_mean(s.lme_close_price, window=48)
    sma02= ts_mean(s.lme_close_price, window=32)
    cp=s.lme_close_price

    result = (sma01 < sma02) & (cp < sma01) & (cp < sma02)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (sma01 >= sma02) & (cp >= sma01) & (cp >= sma02)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result  * s.lme_volume) + (result2  * s.lme_volume )