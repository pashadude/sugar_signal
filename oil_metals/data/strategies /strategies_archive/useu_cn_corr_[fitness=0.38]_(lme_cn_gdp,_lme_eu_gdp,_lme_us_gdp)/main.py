config = AlphaConfig()
def useu_cn_corr(s:Streams):
    """
    The economic situation in the US and the EU significantly influences China's production plans,
    as these regions are China's main trade partners, accounting for approximately 40% of its total export production.
    The correlation between U.S. and EU GDP growth versus China's GDP growth reflects global economic divergence.
    Negative signal suggests decoupling, potentially reducing demand for base metals globally.
    """
    eu_gdp = ts_pct_change(ts_log10(ts_ffill(s.lme_eu_gdp)), periods=month_4)
    us_gdp = ts_pct_change(ts_log10(ts_ffill(s.lme_us_gdp)), periods=month_4)
    cn_gdp = ts_pct_change(ts_log10(ts_ffill(s.lme_cn_gdp)), periods=month_4)
    return - correlation((us_gdp+eu_gdp), cn_gdp, window=month_7)