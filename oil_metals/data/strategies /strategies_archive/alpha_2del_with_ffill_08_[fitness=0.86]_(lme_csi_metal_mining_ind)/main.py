config = AlphaConfig()
def alpha_2del_with_ffill_08(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta vs delta, ts_ffill, lme_csi_metal_mining_ind.
    """
    return delta(ts_ffill(s.lme_csi_metal_mining_ind), period=13) - delta(ts_ffill(s.lme_csi_metal_mining_ind), period=17)