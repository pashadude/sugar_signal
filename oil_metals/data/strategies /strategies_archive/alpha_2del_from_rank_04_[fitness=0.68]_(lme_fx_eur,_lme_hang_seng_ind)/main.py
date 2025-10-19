config = AlphaConfig()
def alpha_2del_from_rank_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta of optimized correlation: lme_fx_eur and lme_hang_seng_ind.
    """
    return delta(ts_rank(s.lme_fx_eur, window=12),period=12) - delta(ts_rank(s.lme_hang_seng_ind, window=7),period=7)