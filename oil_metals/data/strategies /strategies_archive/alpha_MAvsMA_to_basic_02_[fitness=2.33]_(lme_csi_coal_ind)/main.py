config = AlphaConfig()
def alpha_MAvsMA_to_basic_02(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of moving averages to basic (lme_csi_coal_ind) with ts_ffill.
    """
    return (ts_mean(ts_ffill(s.lme_csi_coal_ind), window=29) - ts_mean(ts_ffill(s.lme_csi_coal_ind), window=15))/(ts_ffill(s.lme_csi_coal_ind))