config = AlphaConfig()
def us_gdp_mom(s:Streams):
    """
    The U.S. GDP Momentum measures short-term GDP growth relative to long-term trends.
    A negative signal suggests slowing economic momentum, which could weaken base metal demand and prices.
    """
    us_gdp_pct = ts_pct_change(ts_ffill(s.lme_us_gdp), periods=month)
    us_gdp_ma_short = ts_mean(us_gdp_pct, window=month_2)
    us_gdp_ma_long = ts_mean(us_gdp_pct, window=half)
    us_gdp_momentum = zscore((us_gdp_ma_short - us_gdp_ma_long), window=half)
    return - us_gdp_momentum