config = AlphaConfig()
def alpha_2del_with_ffill_02(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta vs delta, ts_ffill, basis - lme_csi_env_protect_ind.
    """
    return delta(ts_rank(ts_ffill(s.lme_csi_env_protect_ind), window=9), period=9) - delta(ts_rank(ts_ffill(s.lme_csi_env_protect_ind), window=2), period=2)