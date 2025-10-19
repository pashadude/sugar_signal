config = AlphaConfig()
def alpha_log_equity_comb(s: Streams):
    """
    Hypothesis: The logarithm of equity indices from China, Japan, and the EU can reflect the strength of the global economy,
    with increased demand for base metals potentially driving their prices higher.
    """
    cn_equity = s.lme_cn_equity_ind
    eu_equity = s.lme_eu_equity_ind
    jpy_equity = s.lme_jpy_equity_ind
    log_equity_comb = log((cn_equity + eu_equity + jpy_equity), 10)
    return log_equity_comb