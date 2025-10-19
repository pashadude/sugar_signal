config = AlphaConfig()
def alpha_MAvsMA_05(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of moving averages (lme_brent_oil) with ts_ffill.
    """
    return (ts_mean(ts_ffill(s.lme_brent_oil), window=5) - ts_mean(ts_ffill(s.lme_brent_oil), window=13))