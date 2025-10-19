config = AlphaConfig()
def alpha_cn_eu_corr(s: Streams):
    """
    Hypothesis: Positive correlation indicates the strength of global trade between EU and China as major trade partners,
    and they are two major consumers of base metals in production around the world.
    """
    cn_equity_ind = s.lme_cn_equity_ind
    eu_equity_ind = s.lme_eu_equity_ind
    cn_eu_corr = correlation(cn_equity_ind, eu_equity_ind)
    return cn_eu_corr