config = AlphaConfig()
def alpha_2del_with_rank_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta(lme_high_price) vs delta(lme_low_price), ts_rank.
    """
    return delta(ts_rank(s.lme_high_price, window=10), period=10) - delta(ts_rank(s.lme_low_price, window=4), period=4)