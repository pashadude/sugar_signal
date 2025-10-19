config = AlphaConfig()
def alpha_2corr_bric(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Corrected correlation, basis - lme_ftse_bric_50_ind.
    """
    return (correlation(s.lme_us_vix, s.lme_ftse_bric_50_ind, window=33) - correlation(s.lme_ftse_bric_50_ind, s.lme_eu_equity_ind, window=3))