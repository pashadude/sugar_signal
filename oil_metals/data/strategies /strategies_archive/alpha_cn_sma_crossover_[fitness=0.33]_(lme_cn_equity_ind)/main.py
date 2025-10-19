config = AlphaConfig()
def alpha_cn_sma_crossover(s: Streams):
    """
    Hypothesis: An excess long-term trend in the Chinese equity market (SSE Composite) over the short-term trend
    indicates heightened industrial activity, potentially driving increased demand for base metals.
    and influencing a rise in their prices.
    """
    cn_equity_ind = s.lme_cn_equity_ind
    cn_equity_ind = zscore(cn_equity_ind, window=week_2)
    cn_equity_ind_ma42 = ts_mean(cn_equity_ind, window=week_2)
    cn_equity_ind_ma63 = ts_mean(cn_equity_ind, window=month)
    cn_equity_ind_sam_diff = cn_equity_ind_ma63 - cn_equity_ind_ma42
    return cn_equity_ind_sam_diff