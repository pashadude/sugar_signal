config = AlphaConfig()
def us_gdp_close_corr(s:Streams):
    """
    Positive correlation between US GDP and close price growth rates could potentially
    have a negative effect on base metal price due to base metal supply surplus on the market.
    """
    us_gdp_pct = ts_pct_change(ts_ffill(s.lme_us_gdp), periods=quarterly)
    close_price = s.lme_close_price
    return - correlation(us_gdp_pct, close_price, window=month)