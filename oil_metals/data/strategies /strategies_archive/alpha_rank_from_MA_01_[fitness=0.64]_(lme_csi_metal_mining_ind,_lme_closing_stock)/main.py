config = AlphaConfig()
def alpha_rank_from_MA_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of opitmized averages: lme_csi_metal_mining_ind and lme_closing_stock.
    """
    return -ts_rank(ts_mean(s.lme_csi_metal_mining_ind, window=10), window=10) + ts_rank(ts_mean(s.lme_closing_stock, window=7), window=7)