config = AlphaConfig()
def us_constr_gdp_ratio(s:Streams):
    """
    The Construction GDP Ratio tracks short-term vs. long-term U.S. construction spending trends.
    Positive signal suggests rising construction momentum, supporting base metal prices,
    while a negative signal indicates slowing activity, pressuring prices.
    """
    us_constr_gdp_ratio = safe_div(
        zscore(ts_ffill(s.lme_us_constr_spend), window=month_4),
        zscore(ts_ffill(s.lme_us_constr_spend), window=month_7))
    return zscore(us_constr_gdp_ratio, window=half)