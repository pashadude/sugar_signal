config = AlphaConfig()
def alpha_2del_with_ffill_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta vs delta, ts_ffill, basis - lme_csi_env_protect_ind.
    """
    return delta((ts_ffill(s.lme_csi_env_protect_ind)), period=10) - delta((ts_ffill(s.lme_csi_env_protect_ind)), period=22)