config = AlphaConfig()
def alpha_2del_with_ffill_09(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta vs delta, ts_ffill, lme_csi_non_fer_metal_ind.
    """
    return delta(ts_ffill(s.lme_csi_non_fer_metal_ind), period=8) - delta(ts_ffill(s.lme_csi_non_fer_metal_ind), period=14)