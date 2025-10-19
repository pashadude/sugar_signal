config = AlphaConfig()
def cn_gdp_mom(s:Streams):
    """
    Positive normalization of China's GDP momentum signals stronger industrial demand (the largest base metal consumer)
    and rising base metal prices, while negative normalization suggests a slowdown and falling prices.
    """
    cn_gdp_pct = ts_pct_change(ts_ffill(s.lme_cn_gdp), periods=quarterly)
    cn_gdp_ma_short = ts_mean(cn_gdp_pct, window=half)
    cn_gdp_ma_long = ts_mean(cn_gdp_pct, window=month_9)
    cn_gdp_momentum = zscore((cn_gdp_ma_short - cn_gdp_ma_long), window=half)
    return cn_gdp_momentum