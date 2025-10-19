config = AlphaConfig()
def m2_cn_gdp_corr(s:Streams):
    """
    The signal measures the correlation between U.S. money supply (M2) and China's GDP growth.
    Negative signal suggests weaker monetary support aligning with slower Chinese economic growth, pressuring base metal demand.
    """
    m2_cn_gdp_corr = correlation(
        ts_ffill(s.lme_us_mon_sup),
        ts_ffill(s.lme_cn_gdp),
        window=month_9)
    return - ts_mean(m2_cn_gdp_corr, window=month)