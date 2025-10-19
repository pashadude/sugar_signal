config = AlphaConfig()
def alpha_2del_with_ffill_05(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta vs delta, ts_ffill, lme_cn_pmi.
    """
    return delta(ts_ffill(s.lme_cn_pmi), period=3) - delta(ts_ffill(s.lme_cn_pmi),  period=9)