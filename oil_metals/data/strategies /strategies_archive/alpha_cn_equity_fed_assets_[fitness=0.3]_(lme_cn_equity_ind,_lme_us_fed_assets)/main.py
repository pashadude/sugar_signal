config = AlphaConfig()
def alpha_cn_equity_fed_assets(s: Streams):
    """
    Hypothesis: High China equity index levels combined with elevated FED assets indicate a strong Chinese economy
    and ongoing U.S. monetary stimulus, which may lead to sustained increases in commodity prices.
    """
    cn_equity = s.lme_cn_equity_ind
    fed_assets = ts_ffill(s.lme_us_fed_assets)
    cn_equity_ma_15 = ts_mean(cn_equity, window=week_3)
    fed_assets_ma_15 = ts_mean(fed_assets, window=week_3)
    return cn_equity_ma_15 + fed_assets_ma_15