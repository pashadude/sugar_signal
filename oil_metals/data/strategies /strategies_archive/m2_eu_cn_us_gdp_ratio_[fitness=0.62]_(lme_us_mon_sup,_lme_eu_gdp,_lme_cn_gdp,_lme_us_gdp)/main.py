config = AlphaConfig()
def m2_eu_cn_us_gdp_ratio(s:Streams):
    """
    The M2-to-GDP Ratio compares U.S. money supply growth (M2) to GDP growth in the U.S., EU, and China.
    A lower ratio (negative signal) suggests stronger economic growth relative to monetary expansion, potentially boosting base metal demand,
    while a higher ratio indicates weaker growth or excessive liquidity, pressuring prices.
    """
    m2_eu_cn_us_gdp_ratio = safe_div(
        zscore(delta(ts_ffill(s.lme_us_mon_sup), period=month_2),window=month_4),
        zscore(
            (delta(ts_ffill(s.lme_eu_gdp), period=month_4) +
            delta(ts_ffill(s.lme_cn_gdp), period=month_4) +
            delta(ts_ffill(s.lme_us_gdp), period=month_4)),
        window=month_4))
    return - m2_eu_cn_us_gdp_ratio