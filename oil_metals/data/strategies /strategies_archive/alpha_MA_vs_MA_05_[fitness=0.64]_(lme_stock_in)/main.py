config = AlphaConfig()
def alpha_MA_vs_MA_05(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of averages: lme_stock_in in different timeframes.
    """
    return ts_mean(s.lme_stock_in, window=16) - ts_mean(s.lme_stock_in, window=2)