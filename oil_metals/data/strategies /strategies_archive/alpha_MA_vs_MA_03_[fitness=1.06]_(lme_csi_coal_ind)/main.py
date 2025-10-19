config = AlphaConfig()
def alpha_MA_vs_MA_03(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of averages: lme_csi_coal_ind in different timeframes.
    """
    return ts_mean(s.lme_csi_coal_ind, window=22) - ts_mean(s.lme_csi_coal_ind, window=15)