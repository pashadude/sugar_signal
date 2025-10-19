config = AlphaConfig()
def alpha_2del_from_rank_03(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta of optimized correlation: lme_hang_seng_ind and lme_msci_europe_pr_ind.
    """
    return delta(ts_rank(s.lme_hang_seng_ind, window=18),period=18) - delta(ts_rank(s.lme_msci_europe_pr_ind, window=20),period=20)