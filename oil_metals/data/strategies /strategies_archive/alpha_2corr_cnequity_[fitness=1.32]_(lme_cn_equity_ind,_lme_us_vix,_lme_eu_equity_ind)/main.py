config = AlphaConfig()
def alpha_2corr_cnequity(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Corrected correlation, basis - lme_cn_equity_ind.
    """
    return (correlation(s.lme_cn_equity_ind, s.lme_eu_equity_ind, window=20) - correlation(s.lme_us_vix, s.lme_cn_equity_ind, window=33))