config = AlphaConfig()
def us_cn_gdp_corr(s:Streams):
    """
    The US and China are the most strong economies in the world, the positive correlation between percent change
    of the US and China GDP suggests the more intensive demand for base metal with their corresponding price increase.
    """
    us_gdp_pct = ts_pct_change(ts_log10(ts_ffill(s.lme_us_gdp)), periods=quarterly)
    cn_gdp_pct = ts_pct_change(ts_log10(ts_ffill(s.lme_cn_gdp)), periods=quarterly)
    return correlation(us_gdp_pct, cn_gdp_pct, window=half)