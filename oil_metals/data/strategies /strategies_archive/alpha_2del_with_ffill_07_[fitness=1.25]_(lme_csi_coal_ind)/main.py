config = AlphaConfig()
def alpha_2del_with_ffill_07(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta vs delta, ts_ffill, lme_csi_coal_ind.
    """
    return delta(ts_ffill(s.lme_csi_coal_ind), period=11) - delta(ts_ffill(s.lme_csi_coal_ind), period=17)