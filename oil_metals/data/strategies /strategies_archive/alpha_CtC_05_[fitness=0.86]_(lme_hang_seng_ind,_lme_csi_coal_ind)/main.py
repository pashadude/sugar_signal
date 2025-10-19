config = AlphaConfig()
def alpha_CtC_05(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Correlation to Correlation  (lme_hang_seng_ind and lme_csi_coal_ind) with ts_ffill.
    """
    return correlation(ts_ffill(s.lme_hang_seng_ind), ts_ffill(s.lme_csi_coal_ind), window=16) / correlation(ts_ffill(s.lme_hang_seng_ind), ts_ffill(s.lme_csi_coal_ind), window=19)