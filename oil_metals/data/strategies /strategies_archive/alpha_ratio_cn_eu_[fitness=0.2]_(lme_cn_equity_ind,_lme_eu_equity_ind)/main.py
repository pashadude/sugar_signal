config = AlphaConfig()
def alpha_ratio_cn_eu(s: Streams):
    """
    Hypothesis: Dominance in industrial production from China suggests robust European and global consumer demand,
    driving continued demand for base metals and potentially leading to an increase in their prices.
    """
    cn_equity_ind = s.lme_cn_equity_ind
    eu_equity_ind = s.lme_eu_equity_ind
    cn_eu_ratio = safe_div(cn_equity_ind, eu_equity_ind)
    return cn_eu_ratio