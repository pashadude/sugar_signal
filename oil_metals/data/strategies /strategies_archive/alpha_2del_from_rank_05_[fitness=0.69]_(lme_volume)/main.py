config = AlphaConfig()
def alpha_2del_from_rank_05(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta of optimized correlation: lme_volume in different timeframes.
    """
    return delta(ts_rank(s.lme_volume, window=7),period=7) - delta(ts_rank(s.lme_volume, window=16),period=16)