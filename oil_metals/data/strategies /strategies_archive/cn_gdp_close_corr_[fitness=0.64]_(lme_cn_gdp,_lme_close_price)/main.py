config = AlphaConfig()
def cn_gdp_close_corr(s:Streams):
    """
    A positive correlation between close price and moving averages of China GDP growth rates
    could potentially lead to a decrease in base metal demand and prices.
    """
    cn_gdp_pct = ts_pct_change(ts_ffill(s.lme_cn_gdp), periods=quarterly)
    close_price = s.lme_close_price
    return - correlation(ts_mean(cn_gdp_pct, window=half), close_price, window=month_2)