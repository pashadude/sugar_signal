config = AlphaConfig()
def cn_eu_gdp_close_corr(s:Streams):
    """
    The Positive value of correlation between cumulative the EU and China GDP
    and close price growth rates has a negative effect to base metal prices.
    """
    cn_gdp_pct = ts_pct_change(ts_ffill(s.lme_cn_gdp), periods=quarterly)
    eu_gdp_pct = ts_pct_change(ts_ffill(s.lme_eu_gdp), periods=quarterly)
    close_price = s.lme_close_price
    return - correlation(ts_mean((cn_gdp_pct+eu_gdp_pct), window=half), close_price, window=month_2)