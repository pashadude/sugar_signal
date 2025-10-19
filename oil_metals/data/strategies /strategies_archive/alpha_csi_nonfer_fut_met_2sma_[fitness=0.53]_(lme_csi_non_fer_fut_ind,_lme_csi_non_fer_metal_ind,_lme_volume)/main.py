config = AlphaConfig()
def alpha_csi_nonfer_fut_met_2sma(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: lme_csi_non_fer_metal_ind > SMA (5-day) AND lme_csi_non_fer_fut_ind > SMA (19-day).
    - Short: lme_csi_non_fer_metal_ind <= SMA (5-day) AND lme_csi_non_fer_fut_ind <= SMA (19-day).
    """

    ver1=s.lme_csi_non_fer_metal_ind
    ver2=s.lme_csi_non_fer_fut_ind
    sma1 = ts_mean(ver1, window=5)
    sma2 = ts_mean(ver2, window=19)

    result2 = (ver1 > sma1) & (ver2 > sma2)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, 1)

    result = (ver1 <= sma1) & (ver2 <= sma2)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, -1)
    
    return ( result * s.lme_volume) + (result2  * s.lme_volume )