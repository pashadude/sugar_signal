config = AlphaConfig()
def alpha_CtC_03(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Correlation to Correlation  (lme_eu_cpi and lme_fx_cny) with ts_ffill.
    """
    return correlation(ts_ffill(s.lme_eu_cpi), ts_ffill(s.lme_fx_cny), window=20) / correlation(ts_ffill(s.lme_eu_cpi), ts_ffill(s.lme_fx_cny), window=24)