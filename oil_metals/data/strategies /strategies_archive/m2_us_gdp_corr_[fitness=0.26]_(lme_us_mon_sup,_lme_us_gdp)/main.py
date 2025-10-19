config = AlphaConfig()
def m2_us_gdp_corr(s:Streams):
    """
    Negative correlation between U.S. money supply and U.S. GDP over the last seven months
    suggests weaker monetary support for economic growth, potentially pressuring base metal demand and prices too.
    """
    m2_gdp_corr = correlation(
        ts_ffill(s.lme_us_mon_sup),
        ts_ffill(s.lme_us_gdp),
        window=month_7)
    return - m2_gdp_corr