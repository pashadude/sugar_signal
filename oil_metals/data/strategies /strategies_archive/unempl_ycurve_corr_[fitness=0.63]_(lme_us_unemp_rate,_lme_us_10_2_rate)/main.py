config = AlphaConfig()
def unempl_ycurve_corr(s:Streams):
    """
    Hypothesis: The Unemployment-Yield Curve Correlation measures the link between U.S. unemployment and the 10-2 Treasury yield spread.
    A stronger negative correlation may signal recession risk, weighing on base metal demand.
    """
    ycurve = s.lme_us_10_2_rate
    unemp = ts_ffill(s.lme_us_unemp_rate)
    unemployment_ycurve_corr = correlation(unemp, ycurve, window=week_2)
    return - unemployment_ycurve_corr