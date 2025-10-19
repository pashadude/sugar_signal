config = AlphaConfig()
def alpha_MA_vs_MA_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of averages: lme_stock_out in different timeframes.
    """
    return ts_mean(s.lme_stock_out, window=15) - ts_mean(s.lme_stock_out, window=18)