config = AlphaConfig()
def m2_us_gdp_ratio(s:Streams):
    """
    The U.S. M2-to-GDP Ratio reflects the Federal Reserve's monetary support relative to economic output.
    A higher ratio (more positive signal) indicates tightening liquidity, potentially reducing demand and prices for base metals.
    """
    m2_gdp_ratio = safe_div(
        zscore(delta(ts_ffill(s.lme_us_mon_sup), period=month_2),window=month_4),
        zscore(delta(ts_ffill(s.lme_us_gdp), period=month_4),window=month_4))
    return - m2_gdp_ratio