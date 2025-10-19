config = AlphaConfig()
def alpha_2del_with_ffill_10(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta vs delta, ts_ffill, (lme_hang_seng_ind).
    """
    return delta(ts_ffill(s.lme_hang_seng_ind), period=2) - delta(ts_ffill(s.lme_hang_seng_ind), period=23)