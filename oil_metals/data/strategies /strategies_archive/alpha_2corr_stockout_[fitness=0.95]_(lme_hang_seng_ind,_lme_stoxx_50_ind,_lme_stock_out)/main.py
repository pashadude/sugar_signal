config = AlphaConfig()
def alpha_2corr_stockout(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Corrected correlation, basis - lme_stock_out.
    """
    return (correlation(s.lme_stoxx_50_ind, s.lme_stock_out, window=28) - correlation(s.lme_stock_out, s.lme_hang_seng_ind, window=20))