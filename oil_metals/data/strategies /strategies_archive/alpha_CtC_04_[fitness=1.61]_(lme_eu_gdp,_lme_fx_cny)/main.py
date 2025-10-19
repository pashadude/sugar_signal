config = AlphaConfig()
def alpha_CtC_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Correlation to Correlation  (lme_eu_gdp and lme_fx_cny) with ts_ffill.
    """
    return correlation(ts_ffill(s.lme_eu_gdp), ts_ffill(s.lme_fx_cny), window=28) / correlation(ts_ffill(s.lme_eu_gdp), ts_ffill(s.lme_fx_cny), window=39)