config = AlphaConfig()
def us_constr_gdp_corr(s:Streams):
    """
    The Construction-GDP Correlation measures the relationship between U.S. construction spending and GDP.
    A negative signal suggests weakening construction activity relative to GDP, indicating potential downward pressure on base metal prices,
    while a positive signal implies stronger construction-driven demand, supporting higher prices.
    """
    us_constr_gdp_corr = correlation(
        ts_ffill(s.lme_us_constr_spend),
        ts_ffill(s.lme_us_gdp),
        window=half)
    return - us_constr_gdp_corr