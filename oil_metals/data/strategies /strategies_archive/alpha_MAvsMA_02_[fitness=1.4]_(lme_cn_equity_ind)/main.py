config = AlphaConfig()
def alpha_MAvsMA_02(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of moving averages (lme_cn_equity_ind).
    """
    return (ts_mean(s.lme_cn_equity_ind, window=17) - ts_mean(s.lme_cn_equity_ind, window=14))