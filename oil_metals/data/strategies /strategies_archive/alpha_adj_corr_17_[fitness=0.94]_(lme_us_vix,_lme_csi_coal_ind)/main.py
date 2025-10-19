config = AlphaConfig()
def alpha_adj_corr_17(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_csi_coal_ind and lme_us_vix) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_csi_coal_ind), ts_ffill(s.lme_us_vix), window=41)
    rsi_corr = ts_rsi(corr, period=7)

    result = (rsi_corr < 25)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 75)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return corr + ( corr * (result + result2) )