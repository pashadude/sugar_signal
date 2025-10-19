config = AlphaConfig()
def alpha_2del_from_rank_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta of optimized correlation: lme_cancelled_stock and lme_stock_out.
    """
    return delta(ts_rank(s.lme_cancelled_stock, window=7),period=7) - delta(ts_rank(s.lme_stock_out, window=7),period=7)