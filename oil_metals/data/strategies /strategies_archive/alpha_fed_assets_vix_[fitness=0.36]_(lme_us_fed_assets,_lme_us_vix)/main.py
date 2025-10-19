config = AlphaConfig()
def alpha_fed_assets_vix(s: Streams):
    """
    Hypothesis: In times of high market volatility, central banks' quantitative easing boosts the economy
    by lowering interest rates and increasing the money supply, leading to higher demand for commodities and rising prices.
    Conversely, without such measures, the opposite effect occurs.
    """
    fed_assets = ts_ffill(s.lme_us_fed_assets)
    fed_assets_ma15 = ts_mean(fed_assets, window=week_3)
    vix_ma15 = ts_mean(s.lme_us_vix, window=week_3)
    return zscore((fed_assets_ma15 - vix_ma15), window=week_2)