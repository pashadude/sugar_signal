config = AlphaConfig()
def alpha_rank_from_MA_02(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of opitmized averages: lme_fx_cny and lme_us_vix.
    """
    return ts_rank(ts_mean(s.lme_fx_cny, window=6), window=6) - ts_rank(ts_mean(s.lme_us_vix, window=7), window=7)