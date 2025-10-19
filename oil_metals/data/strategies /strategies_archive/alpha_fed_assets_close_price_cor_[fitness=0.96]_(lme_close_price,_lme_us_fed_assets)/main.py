config = AlphaConfig()
def alpha_fed_assets_close_price_cor(s: Streams):
    """
    Hypothesis: A positive correlation between average 3-weeks values of the Federal Reserve's Assets
    [U.S. treasuries, Mortgage-backed securities, and other financial derivatives] and the closing price
    of base metals signaling increased money supply as well as demand for commodities and a potential rise in prices.
    """
    fed_assets = ts_ffill(s.lme_us_fed_assets)
    fed_assets_ma15 = ts_mean(fed_assets, window=week_3)
    close = s.lme_close_price
    close_ma15 = ts_mean(close, window=week_3)
    return correlation(fed_assets_ma15, close_ma15, window=week_3)