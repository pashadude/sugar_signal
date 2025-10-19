config = AlphaConfig()
def alpha_cn_equity_ind_momentum(s: Streams):
    """
    Hypothesis: Positive momentum in the Chinese equity market (SSE Composite) reflects demand for base metals
    (prices will probably rise) since China is a major consumer.
    """
    cn_equity_ind = s.lme_cn_equity_ind
    cn_equity_ind_ma21 = ts_mean(cn_equity_ind, window=month)
    cn_equity_ind_ma42 = ts_delay(cn_equity_ind_ma21, period=month)
    cn_equity_ind_ma_42_21 = cn_equity_ind_ma42 - cn_equity_ind_ma21
    return zscore(cn_equity_ind_ma_42_21, window=week_2)