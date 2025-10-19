config = AlphaConfig()
def alpha_MA_vs_MA_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of averages: lme_volume in different timeframes.
    """
    return ts_mean(s.lme_volume, window=19) - ts_mean(s.lme_volume, window=12)