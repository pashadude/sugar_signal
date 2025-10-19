config = AlphaConfig()
def alpha_CtC_07(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Correlation to Correlation  (lme_hang_seng_ind and lme_csi_env_protect_ind) with ts_ffill.
    """
    return correlation(ts_ffill(s.lme_hang_seng_ind), ts_ffill(s.lme_csi_env_protect_ind), window=9) / correlation(ts_ffill(s.lme_hang_seng_ind), ts_ffill(s.lme_csi_env_protect_ind), window=14)