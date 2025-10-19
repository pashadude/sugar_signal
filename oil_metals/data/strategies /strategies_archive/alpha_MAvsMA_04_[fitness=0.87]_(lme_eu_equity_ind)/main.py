config = AlphaConfig()
def alpha_MAvsMA_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of moving averages (lme_eu_equity_ind).
    """
    return (ts_mean(s.lme_eu_equity_ind, window=6) - ts_mean(s.lme_eu_equity_ind, window=7))