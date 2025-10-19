config = AlphaConfig()
def alpha_corr_coal_nonfer_MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: postivive correlation (lme_csi_non_fer_metal_ind and lme_csi_coal_ind) * lme_closing_stock <= SMA (3-day).
    - Short: negative correlation (lme_csi_non_fer_metal_ind and lme_csi_coal_ind) * lme_closing_stock > SMA (3-day).
    """

    series1 = s.lme_csi_non_fer_metal_ind
    series2 = s.lme_csi_coal_ind
    ver1=s.lme_closing_stock
    sma1 = ts_mean(ver1, window=3)
    corr = correlation(series1, series2, window=11)

    result = (ver1 <= sma1)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (ver1 > sma1)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )