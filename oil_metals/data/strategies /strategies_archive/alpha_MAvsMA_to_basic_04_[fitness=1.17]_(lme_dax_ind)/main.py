config = AlphaConfig()
def alpha_MAvsMA_to_basic_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of moving averages to basic (lme_dax_ind) with ts_ffill.
    """
    return (ts_mean(ts_ffill(s.lme_dax_ind), window=27) - ts_mean(ts_ffill(s.lme_dax_ind), window=19))/(ts_ffill(s.lme_dax_ind))