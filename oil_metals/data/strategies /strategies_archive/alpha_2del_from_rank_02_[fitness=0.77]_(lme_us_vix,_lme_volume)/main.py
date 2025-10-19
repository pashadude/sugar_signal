config = AlphaConfig()
def alpha_2del_from_rank_02(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta of optimized correlation: lme_us_vix and lme_volume.
    """
    return delta(ts_rank(s.lme_us_vix, window=5),period=5) - delta(ts_rank(s.lme_volume, window=16),period=16)