config = AlphaConfig()
def alpha_MAvsMA_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of moving averages (lme_csi_precs_metal_ind).
    """
    return (ts_mean(s.lme_csi_precs_metal_ind, window=18) - ts_mean(s.lme_csi_precs_metal_ind, window=5))