config = AlphaConfig()
def alpha_currency_fed_assets_cov(s: Streams):
    """
    Hypothesis: A positive ratio of covariance between currency in circulation with federal assets indicates
    additional money supply for a financial system, leading to increase demand for base metals and higher prices.
    """
    cur_in_circ = ts_ffill(s.lme_us_cur_in_circ)
    fed_assets = ts_ffill(s.lme_us_fed_assets)
    cur_in_circ_perc = ts_mean(cur_in_circ, window=week_2)
    fed_assets_perc = ts_mean(fed_assets, window=week_2)
    cur_fed_assets_cov = covariance(cur_in_circ_perc, fed_assets_perc, window=month)
    return cur_fed_assets_cov