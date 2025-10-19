config = AlphaConfig()
def m2_fed_assets_correlation(s:Streams):
    """
    Hypothesis: The M2-Fed Rate Correlation measures the relationship between U.S. money supply (M2) and Federal Reserve asset [QE or strictly monetary policy] growth.
    A negative correlation, indicating diverging liquidity trends, may lead to declining base metal prices.
    """
    m2 = ts_ffill(s.lme_us_mon_sup)
    fed_assets = ts_delay(ts_ffill(s.lme_us_fed_assets), period=week)
    m2_pct = ts_pct_change(m2, periods=month)
    fed_assets_pct = ts_pct_change(fed_assets, periods=month)
    m2_pct_zn = zscore(m2_pct, window=week_2)
    fed_assets_pct_zn = zscore(fed_assets_pct, window=week_2)
    m2_fed_rate_corr =  correlation(m2_pct_zn, fed_assets_pct_zn, window=week_2)
    return - m2_fed_rate_corr