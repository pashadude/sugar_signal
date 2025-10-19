config = AlphaConfig()
def us_cn_vol_corr(s:Streams):
    """
    The signal measures the inverse correlation between U.S. and China GDP volatility.
    Weaker correlation (negative signal) may indicate economic divergence, impacting global demand for base metals.
    """
    us_gdp_std = zscore(ts_stddev(ts_pct_change(ts_ffill(s.lme_us_gdp), periods=quarterly), window=half), window=half)
    cn_gdp_std = zscore(ts_stddev(ts_pct_change(ts_ffill(s.lme_cn_gdp), periods=quarterly), window=half), window=half)
    return - correlation(us_gdp_std, cn_gdp_std, window=quarterly)