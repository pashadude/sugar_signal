config = AlphaConfig()
def alpha_CtC_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Correlation to Correlation  (lme_us_gdp and lme_fx_cny) with ts_ffill.
    """
    return correlation(ts_ffill(s.lme_us_gdp), ts_ffill(s.lme_fx_cny), window=21) / correlation(ts_ffill(s.lme_us_gdp), ts_ffill(s.lme_fx_cny), window=27)