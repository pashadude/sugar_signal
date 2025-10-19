config = AlphaConfig()
def m2_eu_gdp_ratio(s:Streams):
    """
The M2-to-EU GDP Ratio measures U.S. money supply changes relative to EU economic growth.
A declining ratio (negative signal) suggests weakening monetary expansion vs. EU growth
[because the EU is one of the largest consumers for base metals], potentially bearish for base metals.
    """
    m2_eu_gdp_ratio = safe_div(
        zscore(delta(ts_ffill(s.lme_us_mon_sup), period=month_2),window=month_4),
        zscore(delta(ts_ffill(s.lme_eu_gdp), period=month_4),window=month_4))
    return - m2_eu_gdp_ratio