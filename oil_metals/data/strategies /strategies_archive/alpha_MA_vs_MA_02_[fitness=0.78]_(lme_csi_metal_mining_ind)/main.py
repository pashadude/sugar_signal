config = AlphaConfig()
def alpha_MA_vs_MA_02(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of averages: lme_csi_metal_mining_ind in different timeframes.
    """
    return ts_mean(s.lme_csi_metal_mining_ind, window=16) - ts_mean(s.lme_csi_metal_mining_ind, window=5)