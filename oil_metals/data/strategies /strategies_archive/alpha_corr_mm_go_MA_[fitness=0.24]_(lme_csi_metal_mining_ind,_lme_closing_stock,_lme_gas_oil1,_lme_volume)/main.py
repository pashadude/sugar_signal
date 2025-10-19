config = AlphaConfig()
def alpha_corr_mm_go_MA(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: negative correlation (lme_csi_metal_mining_ind and lme_gas_oil1) * lme_closing_stock > SMA (20-day).
    - Short: postivive correlation (lme_csi_metal_mining_ind and lme_gas_oil1) * lme_closing_stock <= SMA (20-day).
    """

    series1 = s.lme_csi_metal_mining_ind
    series2 = s.lme_gas_oil1
    ver1=s.lme_closing_stock
    sma1 = ts_mean(ver1, window=20)
    corr = correlation(series1, series2, window=32)

    result = (ver1 <= sma1)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, -1)

    result2 = (ver1 > sma1)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, 1)

    return ( result * corr * s.lme_volume) + (result2 * corr * s.lme_volume )