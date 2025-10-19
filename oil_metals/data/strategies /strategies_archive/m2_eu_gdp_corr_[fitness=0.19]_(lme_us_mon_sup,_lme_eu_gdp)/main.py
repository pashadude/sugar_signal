config = AlphaConfig()
def m2_eu_gdp_corr(s:Streams):
    """
    The signal captures the inverse relationship between U.S. money supply (M2) and EU GDP.
    A negative correlation suggests that rising U.S. liquidity relative to EU growth may support base metal prices.
    """
    m2_eu_gdp_corr = correlation(
        ts_ffill(s.lme_us_mon_sup),
        ts_ffill(s.lme_eu_gdp),
        window=month_2)
    return - m2_eu_gdp_corr