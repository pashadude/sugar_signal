config = AlphaConfig()
def alpha_adj_corr_15(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_csi_non_fer_metal_ind and lme_us_vix) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_csi_non_fer_metal_ind), ts_ffill(s.lme_us_vix), window=59)
    rsi_corr = ts_rsi(corr, period=30)

    result = (rsi_corr < 40)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 60)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return -corr - ( corr * (result + result2) )