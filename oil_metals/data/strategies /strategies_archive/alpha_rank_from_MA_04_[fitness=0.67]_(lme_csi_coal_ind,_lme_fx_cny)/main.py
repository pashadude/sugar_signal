config = AlphaConfig()
def alpha_rank_from_MA_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of opitmized averages: lme_fx_cny and lme_csi_coal_ind.
    """
    return ts_rank(ts_mean(s.lme_fx_cny, window=6), window=6) - ts_rank(ts_mean(s.lme_csi_coal_ind, window=23), window=23)