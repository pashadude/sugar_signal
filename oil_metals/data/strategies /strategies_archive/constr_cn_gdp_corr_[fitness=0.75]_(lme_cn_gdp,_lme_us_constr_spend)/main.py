config = AlphaConfig()
def constr_cn_gdp_corr(s:Streams):
    """
    The signal measures the correlation between U.S. construction spending and China's GDP growth.
    Negative signal suggests weakening global growth and lower base metal demand,
    while a positive signal indicates stronger demand and rising prices.
    """
    constr_cn_gdp_corr = correlation(
        zscore(delta(ts_ffill(s.lme_us_constr_spend), period=month_4), window=month_4),
        zscore(delta(ts_ffill(s.lme_cn_gdp), period=month_7), window=month_4),
        window=half)
    return - constr_cn_gdp_corr