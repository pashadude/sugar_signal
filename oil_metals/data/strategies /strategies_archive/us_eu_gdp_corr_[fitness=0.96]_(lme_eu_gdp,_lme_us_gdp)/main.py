config = AlphaConfig()
def us_eu_gdp_corr(s:Streams):
    """
    The U.S. and the EU control nearly half of global wealth; therefore, a booming economy in these regions
    can stimulate demand and drive up base metal prices.
    """
    us_gdp_pct = ts_pct_change(ts_log10(ts_ffill(s.lme_us_gdp)), periods=month_4)
    eu_gdp_pct = ts_pct_change(ts_log10(ts_ffill(s.lme_eu_gdp)), periods=month_4)
    return correlation(us_gdp_pct, eu_gdp_pct, window=month_7)