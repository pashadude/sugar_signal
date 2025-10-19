config = AlphaConfig()
def eu_gdp_mom(s:Streams):
    """
    Positive normalization of the European Union's GDP momentum signals stronger industrial demand
    (one of the biggest base metal consumers) and rising base metal prices,
    while negative normalization suggests a slowdown and falling prices
    """
    eu_gdp_pct = ts_pct_change(ts_ffill(s.lme_eu_gdp), periods=quarterly)
    eu_gdp_ma_short = ts_mean(eu_gdp_pct, window=half)
    eu_gdp_ma_long = ts_mean(eu_gdp_pct, window=month_9)
    eu_gdp_momentum = zscore((eu_gdp_ma_short - eu_gdp_ma_long), window=half)
    return eu_gdp_momentum