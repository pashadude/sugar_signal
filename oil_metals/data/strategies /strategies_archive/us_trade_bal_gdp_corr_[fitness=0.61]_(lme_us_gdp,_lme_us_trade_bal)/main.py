config = AlphaConfig()
def us_trade_bal_gdp_corr(s:Streams):
    """
    The Trade Balance-GDP Correlation measures the relationship between U.S. trade balance and U.S. GDP.
    A negative signal (weaker correlation) suggests worsening trade conditions, likely leading to declining base metal prices.
    """
    us_trade_bal_gdp_corr = correlation(
        zscore(ts_ffill(s.lme_us_trade_bal), window=month_4),
        zscore(ts_ffill(s.lme_us_gdp), window=month_7),
        window=month_9)
    return - us_trade_bal_gdp_corr