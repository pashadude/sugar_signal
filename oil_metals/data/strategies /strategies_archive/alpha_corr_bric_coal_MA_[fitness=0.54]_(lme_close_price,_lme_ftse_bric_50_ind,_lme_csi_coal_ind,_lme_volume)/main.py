config = AlphaConfig()
def alpha_corr_bric_coal_MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: postivive correlation (lme_ftse_bric_50_ind and lme_csi_coal_ind) * lme_close_price <= SMA (11-day).
    - Short: negative correlation (lme_ftse_bric_50_ind and lme_csi_coal_ind) * lme_close_price > SMA (11-day).
    """
    
    series1 = s.lme_ftse_bric_50_ind
    series2 = s.lme_csi_coal_ind
    ver1=s.lme_close_price
    sma1 = ts_mean(ver1, window=11)
    corr = correlation(series1, series2, window=27)

    result = (ver1 <= sma1)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, -1)

    result2 = (ver1 > sma1)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, 1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )