config = AlphaConfig()
def us_eu_cn_gdp_unemp_corr(s:Streams):
    """
    The correlation between U.S. unemployment and global GDP (U.S., EU, and China) reflects economic health.
    A negative correlation suggests strong GDP growth reduces unemployment, boosting base metal demand,
    while a positive correlation may indicate weaker economic conditions.
    """
    us_unemp = ts_ffill(s.lme_us_unemp_rate)
    us_gdp = ts_ffill(s.lme_eu_gdp)
    eu_gdp = ts_ffill(s.lme_eu_gdp)
    cng_gdp = ts_ffill(s.lme_cn_gdp)
    gl_gdp = (us_gdp + eu_gdp + cng_gdp)
    us_eu_cn_gdp_unemp_corr = correlation(us_unemp, gl_gdp, window=month_9)
    return - us_eu_cn_gdp_unemp_corr