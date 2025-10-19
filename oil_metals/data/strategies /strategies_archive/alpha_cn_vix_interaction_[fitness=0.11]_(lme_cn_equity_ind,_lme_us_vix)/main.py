config = AlphaConfig()
def alpha_cn_vix_interaction(s: Streams):
    """
    Hypothesis: Positive value shows strength of the chinese economy (adjusted by global volatility level)
    and the negative value indicates instability around the globe.
    """
    cn_equity_ind = s.lme_cn_equity_ind
    us_vix = s.lme_us_vix
    us_vix_ma10 = ts_mean(us_vix, window=week_2)
    cn_equity_vix = (cn_equity_ind - us_vix_ma10)
    return zscore(cn_equity_vix, window=week_2)