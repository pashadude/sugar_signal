config = AlphaConfig()
def alpha_rank_from_MA_03(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of opitmized averages: lme_hang_seng_ind and lme_us_vix.
    """
    return ts_rank(ts_mean(s.lme_hang_seng_ind, window=5), window=5) - ts_rank(ts_mean(s.lme_us_vix, window=7), window=7)