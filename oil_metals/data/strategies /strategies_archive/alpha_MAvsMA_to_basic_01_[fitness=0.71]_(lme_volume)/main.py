config = AlphaConfig()
def alpha_MAvsMA_to_basic_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance between moving averages to basic (lme_volume).
    """
    return (ts_mean(s.lme_volume, window=19) - ts_mean(s.lme_volume, window=12))/s.lme_volume