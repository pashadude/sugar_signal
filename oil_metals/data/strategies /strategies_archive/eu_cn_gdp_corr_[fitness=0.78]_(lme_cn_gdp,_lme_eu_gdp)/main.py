config = AlphaConfig()
def eu_cn_gdp_corr(s:Streams):
    """
    The negative correlation between EU and China GDP growth rates indicates divergent economic trends.
    A weaker correlation suggests reduced global economic synchronization and increased financial speculation,
    which may influence base metal prices.
    """
    eu_gdp_pct = ts_pct_change(ts_log10(ts_ffill(s.lme_eu_gdp)), periods=month_4)
    cn_gdp_pct = ts_pct_change(ts_log10(ts_ffill(s.lme_cn_gdp)), periods=month_4)
    return - correlation(eu_gdp_pct, cn_gdp_pct, window=month_7)