config = AlphaConfig()
def m2_cn_gdp_ratio(s:Streams):
    """
    The M2-to-China GDP Ratio measures U.S. money supply growth against China's GDP growth.
    A negative signal suggests rising U.S. liquidity relative to China’s economy, potentially weakening base metal prices,
    while a positive signal indicates stronger Chinese economic growth, supporting higher base metal prices.
    """
    m2_cn_gdp_ratio = safe_div(
        zscore(delta(ts_ffill(s.lme_us_mon_sup), period=month_2),window=month_4),
        zscore(delta(ts_ffill(s.lme_cn_gdp), period=month_4),window=month_4))
    return - m2_cn_gdp_ratio