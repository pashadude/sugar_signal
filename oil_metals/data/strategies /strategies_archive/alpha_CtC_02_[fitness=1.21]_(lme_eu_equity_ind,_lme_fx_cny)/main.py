config = AlphaConfig()
def alpha_CtC_02(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Correlation to Correlation  (lme_eu_equity_ind and lme_fx_cny) with ts_ffill.
    """
    return correlation(ts_ffill(s.lme_eu_equity_ind), ts_ffill(s.lme_fx_cny), window=27) / correlation(ts_ffill(s.lme_eu_equity_ind), ts_ffill(s.lme_fx_cny), window=34)