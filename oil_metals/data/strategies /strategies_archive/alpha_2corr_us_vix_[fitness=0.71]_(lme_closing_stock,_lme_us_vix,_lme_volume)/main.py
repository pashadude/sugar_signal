config = AlphaConfig()
def alpha_2corr_us_vix(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Corrected correlation, basis - lme_us_vix.
    """
    return (correlation(s.lme_volume, s.lme_us_vix, window=18) - correlation(s.lme_closing_stock, s.lme_us_vix, window=24))