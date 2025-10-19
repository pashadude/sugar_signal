config = AlphaConfig()
def alpha_MAvsMA_to_basic_03(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Variance of moving averages to basic (lme_eu_gdp) with ts_ffill.
    """
    return (ts_mean(ts_ffill(s.lme_eu_gdp), window=2) - ts_mean(ts_ffill(s.lme_eu_gdp), window=3))/(ts_ffill(s.lme_eu_gdp))